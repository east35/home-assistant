"""Restore dashboard configs from a backup directory.

Usage:
    python3 audits/dashboards_restore.py audits/backups/dashboards_<timestamp>
"""
import json
import os
import sys
import threading

import websocket  # type: ignore

TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkZTI5NzU3Njc1MmM0ZDk0OWRmNmJjZTMwMWYxZTUzNyIsImlhdCI6MTc3ODI1NDc4NywiZXhwIjoyMDkzNjE0Nzg3fQ.oW9kSrRxyct9dy3m0ZNx_0i3b7sbySsjTW5vYURdD4Q'
WS_URL = 'ws://192.168.4.179:8123/api/websocket'


def restore_dashboards(backup_dir):
    if not os.path.isdir(backup_dir):
        print(f"Backup directory not found: {backup_dir}")
        sys.exit(1)

    # Map filename → url_path. lovelace.json restores the default dashboard.
    targets = []
    for fname in sorted(os.listdir(backup_dir)):
        if not fname.endswith('.json'):
            continue
        path = os.path.join(backup_dir, fname)
        with open(path) as f:
            cfg = json.load(f)
        stem = fname[:-len('.json')]
        url_path = None if stem == 'lovelace' else stem
        targets.append((url_path, cfg))

    if not targets:
        print(f"No .json files in {backup_dir}")
        sys.exit(1)

    done = threading.Event()
    pending = {}
    msg_id = [1]
    results = {}

    def on_message(ws, message):
        msg = json.loads(message)
        t = msg.get('type')
        if t == 'auth_required':
            ws.send(json.dumps({'type': 'auth', 'access_token': TOKEN}))
        elif t == 'auth_ok':
            for url_path, cfg in targets:
                cid = msg_id[0]; msg_id[0] += 1
                pending[cid] = url_path or 'lovelace'
                payload = {
                    'id': cid,
                    'type': 'lovelace/config/save',
                    'config': cfg,
                }
                if url_path is not None:
                    payload['url_path'] = url_path
                ws.send(json.dumps(payload))
        elif t == 'result':
            rid = msg['id']
            label = pending.pop(rid)
            if msg.get('success'):
                print(f"  ✓ {label}: restored")
                results[label] = True
            else:
                print(f"  ✗ {label}: {msg.get('error')}")
                results[label] = False
            if not pending:
                done.set()

    def on_error(ws, err):
        print(f"WS Error: {err}")
        done.set()

    ws = websocket.WebSocketApp(WS_URL, on_message=on_message, on_error=on_error)
    th = threading.Thread(target=ws.run_forever); th.daemon = True; th.start()
    done.wait(timeout=20); ws.close()

    ok = sum(1 for v in results.values() if v)
    print(f"Restore: {ok}/{len(targets)} dashboards restored from {backup_dir}")
    return ok == len(targets)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(0 if restore_dashboards(sys.argv[1]) else 1)

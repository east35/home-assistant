"""Snapshot current HA dashboard configs to audits/backups/<timestamp>/.

Usage:
    python3 audits/dashboards_backup.py            # writes a fresh snapshot
    from dashboards_backup import backup_dashboards  # used by build_dashboards.py
"""
import json
import os
import sys
import threading
from datetime import datetime

import websocket  # type: ignore

TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkZTI5NzU3Njc1MmM0ZDk0OWRmNmJjZTMwMWYxZTUzNyIsImlhdCI6MTc3ODI1NDc4NywiZXhwIjoyMDkzNjE0Nzg3fQ.oW9kSrRxyct9dy3m0ZNx_0i3b7sbySsjTW5vYURdD4Q'
WS_URL = 'ws://192.168.4.179:8123/api/websocket'

# url_path values to back up. None = the default `lovelace` dashboard.
DASHBOARDS = ['dashboard-mushroom', 'dashboard-tablet', None]

BACKUP_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')


def _filename_for(url_path):
    return f"{url_path or 'lovelace'}.json"


def backup_dashboards(out_dir=None):
    """Fetch each dashboard config and write to out_dir. Returns out_dir path."""
    if out_dir is None:
        ts = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        out_dir = os.path.join(BACKUP_ROOT, f'dashboards_{ts}')
    os.makedirs(out_dir, exist_ok=True)

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
            for url_path in DASHBOARDS:
                cid = msg_id[0]; msg_id[0] += 1
                pending[cid] = url_path
                payload = {'id': cid, 'type': 'lovelace/config'}
                if url_path is not None:
                    payload['url_path'] = url_path
                ws.send(json.dumps(payload))
        elif t == 'result':
            rid = msg['id']
            url_path = pending.pop(rid)
            label = url_path or 'lovelace'
            if msg.get('success'):
                cfg = msg.get('result') or {}
                path = os.path.join(out_dir, _filename_for(url_path))
                with open(path, 'w') as f:
                    json.dump(cfg, f, indent=2)
                size = os.path.getsize(path)
                print(f"  ✓ {label}: {size} bytes → {path}")
                results[label] = True
            else:
                err = msg.get('error', {})
                print(f"  ✗ {label}: {err}")
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
    print(f"Backup: {ok}/{len(DASHBOARDS)} dashboards saved to {out_dir}")
    return out_dir


if __name__ == '__main__':
    out = backup_dashboards()
    print(f"\nRestore with: python3 audits/dashboards_restore.py {out}")
    sys.exit(0)

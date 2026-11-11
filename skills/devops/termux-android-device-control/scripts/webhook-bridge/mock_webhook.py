"""mock_webhook.py - stand-in for an automation app's webhook trigger.

Prove the Termux half of the bridge before a human spends 15-20 taps building macros:
    python3 mock_webhook.py 18080 &
    BASE="http://127.0.0.1:18080/trigger" ./mdr.sh tap "Tetapan"
    # -> TERIMA: {"act": "tap", "text": "Tetapan"}

A matching log line means curl, --data-urlencode, spaces and non-ASCII text all survive.
A 200 from this mock is NOT evidence that the phone can be tapped.
"""
import sys
import json
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 18080


class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = parse_qs(urlparse(self.path).query)
        flat = {k: v[0] for k, v in q.items()}
        print("TERIMA:", json.dumps(flat, ensure_ascii=False), flush=True)
        body = json.dumps({"ok": True, "received": flat}, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


with socketserver.TCPServer(("127.0.0.1", PORT), H) as srv:
    print(f"mock webhook listening on 127.0.0.1:{PORT}", flush=True)
    srv.serve_forever()

import json
import signal
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

CONFIG = json.loads(open("config.json").read())

REPLICA_ID = None
REPLICA_PORT = None
SALDO_DEFAULT = CONFIG["saldo_default"]


class ReplicaHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send_json(self, code, body):
        payload = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/ping":
            self._send_json(200, {"replica_id": REPLICA_ID})

        elif path.startswith("/saldo/"):
            id_tarjeta = path.split("/")[-1]
            self._send_json(200, {
                "replica_id": REPLICA_ID,
                "id_tarjeta": id_tarjeta,
                "saldo": SALDO_DEFAULT
            })

        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/chaos/crash":
            print(f"[{time.time():.3f}] Réplica {REPLICA_ID} recibió /chaos/crash. Terminando proceso.")
            sys.stdout.flush()
            os._exit(0)

        else:
            self._send_json(404, {"error": "not found"})


def main():
    global REPLICA_ID, REPLICA_PORT

    if len(sys.argv) < 3:
        print("Uso: python replica.py <ID> <PUERTO>")
        sys.exit(1)

    REPLICA_ID = sys.argv[1]
    REPLICA_PORT = int(sys.argv[2])

    server = HTTPServer(("0.0.0.0", REPLICA_PORT), ReplicaHandler)
    print(f"[{time.time():.3f}] Réplica {REPLICA_ID} escuchando en puerto {REPLICA_PORT}")
    sys.stdout.flush()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    import os
    main()

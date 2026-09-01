import json
import time
import asyncio
import csv
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import urllib.request
import urllib.error
import threading

CONFIG = json.loads(open("config.json").read())

T = CONFIG["T"]
t_sondeo = CONFIG["t"]
k = CONFIG["k"]
REPLICA_IDS = CONFIG["replica_ids"]
BASE_PORT = CONFIG["base_port"]
DISPATCHER_PORT = CONFIG["dispatcher_port"]

bitacora_lock = threading.Lock()


class ReplicaState:
    def __init__(self, replica_id, host, port):
        self.id = replica_id
        self.host = host
        self.port = port
        self.estado = "VIVA"
        self.fallos_consecutivos = 0

    def url(self, path):
        return f"http://{self.host}:{self.port}{path}"


replicas = [
    ReplicaState(rid, "127.0.0.1", BASE_PORT + i)
    for i, rid in enumerate(REPLICA_IDS)
]


def log_bitacora(mensaje):
    timestamp = time.time()
    line = f"[{timestamp:.3f}] {mensaje}"
    with bitacora_lock:
        with open("bitacora_monitor.log", "a") as f:
            f.write(line + "\n")
            f.flush()
    print(line)
    sys.stdout.flush()


def http_get_sync(url, timeout):
    req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req, timeout=timeout)
    data = resp.read()
    return json.loads(data)


def http_get_async(url, timeout):
    return http_get_sync(url, timeout)


def monitor_sondeo():
    log_bitacora(f"Monitor Ping/Echo iniciado. T={T}s, t={t_sondeo}s, k={k}")
    while True:
        for rep in replicas:
            try:
                resp = http_get_async(rep.url("/ping"), t_sondeo)
                if rep.fallos_consecutivos >= k:
                    log_bitacora(f"{rep.id} CAÍDA -> VIVA (recuperada tras {rep.fallos_consecutivos} fallos consecutivos)")
                rep.fallos_consecutivos = 0
                if rep.estado == "CAIDA":
                    rep.estado = "VIVA"
            except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError, json.JSONDecodeError) as e:
                rep.fallos_consecutivos += 1
                if rep.fallos_consecutivos == k and rep.estado == "VIVA":
                    rep.estado = "CAIDA"
                    log_bitacora(f"{rep.id} VIVA -> CAIDA (tras {k} fallos consecutivos)")
        time.sleep(T)


class DispatcherHandler(BaseHTTPRequestHandler):
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

        if path == "/estado":
            estado = {rep.id: rep.estado for rep in replicas}
            self._send_json(200, estado)

        elif path.startswith("/saldo/"):
            id_tarjeta = path.split("/")[-1]
            vivas = [rep for rep in replicas if rep.estado == "VIVA"]

            if not vivas:
                self._send_json(503, {"error": "no hay replicas disponibles"})
                return

            resultado = None
            lock = threading.Lock()

            def fetch(rep):
                nonlocal resultado
                try:
                    resp = http_get_sync(rep.url(f"/saldo/{id_tarjeta}"), t_sondeo)
                    with lock:
                        if resultado is None:
                            resultado = resp
                except Exception:
                    pass

            threads = [threading.Thread(target=fetch, args=(rep,)) for rep in vivas]
            for t_thread in threads:
                t_thread.start()
            for t_thread in threads:
                t_thread.join(timeout=t_sondeo + 0.1)

            if resultado:
                self._send_json(200, resultado)
            else:
                self._send_json(502, {"error": "todas las replicas fallaron"})

        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        self._send_json(404, {"error": "not found"})


def main():
    for rep in replicas:
        log_bitacora(f"Réplica registrada: {rep.id} en {rep.host}:{rep.port}")

    monitor_thread = threading.Thread(target=monitor_sondeo, daemon=True)
    monitor_thread.start()

    server = HTTPServer(("0.0.0.0", DISPATCHER_PORT), DispatcherHandler)
    print(f"[{time.time():.3f}] Dispatcher escuchando en puerto {DISPATCHER_PORT}")
    sys.stdout.flush()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

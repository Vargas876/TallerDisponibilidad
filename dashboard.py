import json
import os
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote
import urllib.request
import urllib.error

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG = json.loads(open(os.path.join(BASE_DIR, "config.json")).read())

DASHBOARD_PORT = 8000
DISPATCHER_URL = f"http://127.0.0.1:{CONFIG['dispatcher_port']}"
RESULTADOS_DIR = os.path.join(BASE_DIR, "resultados")
BITACORA_FILE = os.path.join(BASE_DIR, "bitacora_monitor.log")
INYECTOR_FILE = os.path.join(BASE_DIR, "timestamp_inyector.log")
DIST_DIR = os.path.join(BASE_DIR, "dashboard-ui", "dist")
CONTENT_TYPES = {
    ".html": "text/html",
    ".js": "application/javascript",
    ".css": "text/css",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".ico": "image/x-icon",
    ".json": "application/json",
    ".woff2": "font/woff2",
    ".map": "application/json",
    ".webmanifest": "application/manifest+json",
}


def leer_bitacora():
    if not os.path.exists(BITACORA_FILE):
        return []
    lineas = []
    with open(BITACORA_FILE, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if line:
                lineas.append(line)
    return lineas


def leer_estado():
    try:
        req = urllib.request.Request(f"{DISPATCHER_URL}/estado")
        resp = urllib.request.urlopen(req, timeout=2)
        return json.loads(resp.read())
    except Exception:
        return None


def leer_inyector():
    if not os.path.exists(INYECTOR_FILE):
        return None
    with open(INYECTOR_FILE, "r") as f:
        lineas = [l.strip() for l in f if l.strip()]
        if not lineas:
            return None
        parts = lineas[-1].split()
        return {"timestamp": float(parts[0]), "replica": parts[1] if len(parts) > 1 else "?"}


def listar_csv():
    if not os.path.exists(RESULTADOS_DIR):
        return []
    return sorted(
        [f for f in os.listdir(RESULTADOS_DIR) if f.lower().endswith(".csv")],
        key=lambda f: os.path.getmtime(os.path.join(RESULTADOS_DIR, f)),
        reverse=True,
    )


def procesar_csv(filename):
    filepath = os.path.join(RESULTADOS_DIR, filename)
    if not os.path.exists(filepath):
        return None

    filas = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        header = f.readline().strip().split(",")
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) < 4:
                continue
            filas.append({
                "t_envio": float(parts[0]),
                "t_resp": float(parts[1]),
                "exito": int(parts[2]),
                "replica": parts[3] if len(parts) > 3 else "",
            })

    if not filas:
        return {"total": 0, "exitosos": 0, "fallidos": 0, "porcentaje": 0, "replicas": {}, "serie": []}

    total = len(filas)
    exitosos = sum(1 for f in filas if f["exito"] == 1)

    # Distribución por réplica (solo exitosas)
    from collections import Counter
    rep_counter = Counter(f["replica"] for f in filas if f["exito"] == 1)

    # Serie temporal por segundo
    t0 = filas[0]["t_envio"]
    buckets = {}
    for f in filas:
        bucket = int(f["t_envio"] - t0)
        b = buckets.setdefault(bucket, {"ok": 0, "fail": 0})
        if f["exito"] == 1:
            b["ok"] += 1
        else:
            b["fail"] += 1

    serie = [
        {"seg": k, "ok": v["ok"], "fail": v["fail"]}
        for k, v in sorted(buckets.items())
    ]

    return {
        "total": total,
        "exitosos": exitosos,
        "fallidos": total - exitosos,
        "porcentaje": round(exitosos / total * 100, 2) if total else 0,
        "replicas": dict(rep_counter),
        "serie": serie,
    }


class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")

    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path, ctype):
        with open(path, "rb") as f:
            body = f.read()
        self._send(200, body, ctype)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _serve_spa(self, fallback=None):
        """Sirve el frontend React compilado (dist). Si no existe, cae al HTML standalone."""
        if os.path.isdir(DIST_DIR):
            filepath = os.path.join(DIST_DIR, fallback or "index.html")
            if os.path.isfile(filepath):
                ext = os.path.splitext(filepath)[1].lower()
                self._send_file(filepath, CONTENT_TYPES.get(ext, "application/octet-stream"))
                return True
        return False

    def do_GET(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        # Endpoints API
        if path == "/api/estado":
            estado = leer_estado()
            if estado is None:
                self._send(200, json.dumps({"disponible": False}))
            else:
                self._send(200, json.dumps({"disponible": True, "estado": estado}))

        elif path == "/api/bitacora":
            self._send(200, json.dumps({"lineas": leer_bitacora()}))

        elif path == "/api/inyector":
            self._send(200, json.dumps(leer_inyector() or {}))

        elif path == "/api/resultados":
            self._send(200, json.dumps({"archivos": listar_csv()}))

        elif path == "/api/resultado":
            params = {} if not parsed.query else dict(
                kv.split("=", 1) for kv in parsed.query.split("&") if "=" in kv
            )
            filename = params.get("archivo", "")
            data = procesar_csv(filename)
            if data is None:
                self._send(404, json.dumps({"error": "archivo no encontrado"}))
            else:
                data["archivo"] = filename
                self._send(200, json.dumps(data))

        # SPA: rutas de la app React
        if path.startswith("/assets/") or path.startswith("/favicon"):
            if not self._serve_spa(fallback=path.lstrip("/")):
                self._send(404, json.dumps({"error": "asset no encontrado"}))
            return

        if path == "/" or path == "/index.html":
            if self._serve_spa():
                return
            # Fallback: dashboard HTML standalone
            self._send_file(os.path.join(BASE_DIR, "dashboard.html"), "text/html")
            return

        # Cualquier otra ruta no-API → SPA fallback (hash/routing del cliente)
        if not path.startswith("/api/"):
            if self._serve_spa():
                return
            self._send(404, json.dumps({"error": "not found"}))
            return

        self._send(404, json.dumps({"error": "not found"}))


def main():
    server = HTTPServer(("0.0.0.0", DASHBOARD_PORT), DashboardHandler)
    print(f"Dashboard escuchando en http://127.0.0.1:{DASHBOARD_PORT}")
    if os.path.isdir(DIST_DIR):
        print(f"  - Frontend React (dist) desde: {DIST_DIR}")
    else:
        print("  - Frontend: dashboard.ui compilada NO encontrada. Corre 'npm run build' en dashboard-ui/")
    print(f"  - Estado réplicas: {DISPATCHER_URL}/estado")
    print(f"  - Bitácora: {BITACORA_FILE}")
    print(f"  - Resultados: {RESULTADOS_DIR}")
    sys.stdout.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

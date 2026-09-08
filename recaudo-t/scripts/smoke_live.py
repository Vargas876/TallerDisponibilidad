"""Smoke test punta a punta: levanta la pila local y valida Live + Resultados.

Levanta réplicas + dispatcher, espera el estado VIVA, arranca el frontend
(Next dev), y comprueba:
  1. HTTP 200 en / (Live), /resultados y /api/metricas
  2. El WebSocket /ws entrega un snapshot con réplicas
  3. Conteo de bytes en cada respuesta

Uso:
  python scripts/smoke_live.py [--no-frontend]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / "config" / ".env")

REPLICA_IDS = ["A", "B", "C", "D", "E", "F"]
NUM_REPLICAS = int(os.getenv("NUM_REPLICAS", "3"))
BASE_PORT = int(os.getenv("REPLICA_BASE_PORT", "8001"))
DISPATCHER_URL = os.getenv("DISPATCHER_URL", "http://127.0.0.1:8000")
PY = os.getenv("SMOKE_PYTHON", str(ROOT / ".venv" / "Scripts" / "python.exe"))


def _log(msg: str) -> None:
    print(f"[smoke] {msg}", flush=True)


def _wget(url: str, timeout: float = 3.0):
    import httpx

    return httpx.get(url, timeout=timeout)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-frontend", action="store_true")
    args = ap.parse_args()

    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    procs: list[subprocess.Popen] = []

    def spawn(cmd: list[str], cwd: Path | None = None, env: dict | None = None, logfile: Path | None = None):
        fh = open(logfile, "w", encoding="utf-8") if logfile else subprocess.DEVNULL
        p = subprocess.Popen(
            cmd,
            cwd=cwd or ROOT,
            env=env or os.environ.copy(),
            stdout=fh,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        procs.append(p)
        return p

    def limpiar() -> None:
        for p in procs:
            try:
                p.terminate()
            except Exception:
                pass
        time.sleep(1.0)
        for p in procs:
            try:
                p.kill()
            except Exception:
                pass
        # next dev deja un "start-server.js" hijo que sobrevive: lo cazamos
        try:
            net = subprocess.run(
                ["netstat", "-ano"], capture_output=True, text=True, timeout=15
            ).stdout.splitlines()
            for line in net:
                if ":3000" in line and "LISTENING" in line:
                    pid = line.strip().split()[-1]
                    if not pid.isdigit():
                        continue
                    info = subprocess.run(
                        ["powershell", "-NoProfile", "-Command",
                         "Get-CimInstance Win32_Process -Filter " +
                         f"'ProcessId={pid}' | Select-Object -ExpandProperty CommandLine"],
                        capture_output=True, text=True, timeout=15,
                    )
                    if "recaudo-t" in (info.stdout or ""):
                        subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
        except Exception:
            pass

    try:
        _log(f"levantando {NUM_REPLICAS} réplicas + dispatcher")
        for i in range(NUM_REPLICAS):
            rid = REPLICA_IDS[i]
            env = os.environ.copy()
            env["REPLICA_ID"] = rid
            env["REPLICA_PORT"] = str(BASE_PORT + i)
            spawn([PY, "backend/replica/main.py"], env=env)
            time.sleep(0.4)
        spawn([PY, "backend/dispatcher/main.py"])

        import httpx

        ok = False
        for _ in range(30):
            try:
                if _wget(f"{DISPATCHER_URL}/estado", 1.0).json()["replicas_viva"] == NUM_REPLICAS:
                    ok = True
                    break
            except Exception:
                pass
            time.sleep(0.5)
        if not ok:
            _log("ERROR: dispatcher no quedó listo con todas las réplicas VIVA")
            return 1
        _log("dispatcher OK, réplicas VIVA")

        if not args.no_frontend:
            _log("arrancando next dev")
            frnt_log = ROOT / "logs" / "frontend_dev.log"
            spawn(
                ["npm.cmd", "run", "dev", "--", "-p", "3000"],
                cwd=ROOT / "frontend",
                logfile=frnt_log,
            )
            base = "http://127.0.0.1:3000"
            lista_ok = False
            for _ in range(60):
                try:
                    if _wget(base, 1.0).status_code == 200:
                        lista_ok = True
                        break
                except Exception:
                    pass
                time.sleep(0.75)
            if not lista_ok:
                _log("ERROR: frontend no respondió en 45s — cola del log:")
                tail = ""
                if frnt_log.exists():
                    lines = frnt_log.read_text(encoding="utf-8", errors="replace").splitlines()
                    tail = "\n".join(lines[-30:])
                print(tail, flush=True)
                return 1
            _log("frontend OK (200)")

            for ruta in ["/", "/resultados", "/api/metricas"]:
                r = _wget(base + ruta, 5.0)
                cuerpo = r.text
                _log(f"{ruta} -> {r.status_code} ({len(cuerpo)} bytes)")
                if r.status_code != 200:
                    return 1
                if ruta == "/":
                    assert "Estado actual del sistema" in cuerpo, "falta hero Live"
                if ruta == "/resultados":
                    assert "Evidencia de resiliencia" in cuerpo, "falta titulo Resultados"
                if ruta == "/api/metricas":
                    data = json.loads(cuerpo)
                    assert data["e1"].get("deteccion"), "faltan métricas e1"
                    _log(f'  api fuente={data["fuente"]} deteccion={data["e1"]["deteccion"]["tiempo_s"]}s')

        _log("probando WebSocket /ws del dispatcher")
        import asyncio
        import websockets

        async def sniffer():
            async with websockets.connect(f"{DISPATCHER_URL.replace('http://', 'ws://')}/ws") as ws:
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=4.0))
                return msg

        msg = asyncio.run(sniffer())
        assert msg.get("type") in ("hello", "snapshot")
        assert len(msg.get("replicas", [])) == NUM_REPLICAS, "snapshot sin réplicas"
        _log(f"WS OK type={msg['type']} réplicas={len(msg['replicas'])}")

    finally:
        limpiar()

    _log("SMOKE OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
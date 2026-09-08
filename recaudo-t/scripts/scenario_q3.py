"""Escenario Q3: réplica que pasa el Ping/Echo pero devuelve saldos rotos.

Levanta 3 réplicas con la réplica B en modo REPLICA_BROKEN_SALDO=1, ejecuta el
cliente de carga y demuestra que:
  - El monitor mantiene a B como VIVA (el ping no detecta el problema).
  - La redundancia activa detecta el saldo roto, descarta la respuesta de B
    del fan-out y el cliente nunca recibe saldos inválidos.
  - B acumula failed_requests pero 0 successful_requests.

Salida: results/q3.json
"""
from __future__ import annotations

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
PY = os.getenv("Q3_PYTHON", str(ROOT / ".venv" / "Scripts" / "python.exe"))
DUR = int(os.getenv("Q3_DURATION", "8"))
RATE = int(os.getenv("CLIENT_RATE", "20"))


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    procs: list[subprocess.Popen] = []

    def spawn(args, env):
        p = subprocess.Popen(args, cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        procs.append(p)
        return p

    try:
        print(f"[q3] réplicas (B con saldo roto) + dispatcher")
        for i in range(NUM_REPLICAS):
            rid = REPLICA_IDS[i]
            env = os.environ.copy()
            env["REPLICA_ID"] = rid
            env["REPLICA_PORT"] = str(BASE_PORT + i)
            env["REPLICA_BROKEN_SALDO"] = "1" if rid == "B" else "0"
            spawn([PY, "backend/replica/main.py"], env)
            time.sleep(0.4)
        spawn([PY, "backend/dispatcher/main.py"], os.environ.copy())

        import httpx

        for _ in range(30):
            try:
                r = httpx.get(f"{DISPATCHER_URL}/estado", timeout=1.0)
                if r.status_code == 200 and r.json()["replicas_viva"] == NUM_REPLICAS:
                    break
            except Exception:
                pass
            time.sleep(0.5)

        csv = ROOT / "results" / "q3.csv"
        csv.parent.mkdir(exist_ok=True)
        p = spawn(
            [PY, "backend/client/client.py", "--out", str(csv), "--duration", str(DUR), "--rate", str(RATE)],
            os.environ.copy(),
        )
        p.wait(timeout=DUR + 30)

        import csv as csvmod

        rows = list(csvmod.DictReader(csv.open(newline="", encoding="utf-8")))
        total = len(rows)
        exitosos = sum(1 for r in rows if int(r["exito"]) == 1)
        invalidos = sum(1 for r in rows if int(r["exito"]) == 1 and r["replica"] == "B")

        estado = httpx.get(f"{DISPATCHER_URL}/estado", timeout=2.0).json()
        repB = next(x for x in estado["replicas"] if x["id"] == "B")

        evidencia = {
            "escenario": "q3",
            "config": {"punica_con_saldo_roto": "B", "duracion_s": DUR, "rate": RATE},
            "cliente": {"total": total, "exitosos": exitosos, "tasa_exito": round(100 * exitosos / total, 2)},
            "entregadas_por_B": invalidos,
            "monitor_ve": {"replica_B_estado": repB["status"], "ping_OK": repB["status"] == "VIVA"},
            "redundancia_B": {"total_requests": repB["total_requests"], "successful_requests": repB["successful_requests"], "failed_requests": repB["failed_requests"]},
        }
        path_salida = ROOT / "results" / "q3.json"
        path_salida.write_text(json.dumps(evidencia, indent=2, ensure_ascii=False), encoding="utf-8")

        print(json.dumps(evidencia, indent=2, ensure_ascii=False))
        assert exitosos == total, "el cliente recibió respuestas inválidas"
        assert repB["status"] == "VIVA", "B no debería estar marcada CAÍDA (el ping no la ve)"
        assert invalidos == 0, "se entregó saldo de la réplica rota"
        assert repB["successful_requests"] == 0 and repB["failed_requests"] == repB["total_requests"], "la redundancia no descartó a B"
        print("[q3] OK — pivote: ping OK pero 0 saldos exitosos por B")
    finally:
        for p in procs:
            try:
                p.terminate()
            except Exception:
                pass
        time.sleep(1)
        for p in procs:
            try:
                p.kill()
            except Exception:
                pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
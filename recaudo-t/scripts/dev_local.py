"""Desarrollo local: levanta réplicas + dispatcher en primer plano.

Al interrumpir (Ctrl+C) termina los procesos lanzados y limpia.

Uso:
  python scripts/dev_local.py
"""
from __future__ import annotations

import os
import signal
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
PY = sys.executable


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    procs: list[subprocess.Popen] = []
    pids_file = ROOT / ".live_pids.txt"

    def spawn(args: list[str], env: dict):
        p = subprocess.Popen(
            args, cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        procs.append(p)
        pids_file.write_text(
            "\n".join(str(p.pid) for p in procs), encoding="utf-8"
        )
        return p

    try:
        for i in range(NUM_REPLICAS):
            rid = REPLICA_IDS[i]
            env = os.environ.copy()
            env["REPLICA_ID"] = rid
            env["REPLICA_PORT"] = str(BASE_PORT + i)
            spawn([PY, "backend/replica/main.py"], env)
            time.sleep(0.4)
        spawn([PY, "backend/dispatcher/main.py"], os.environ.copy())

        import httpx

        url = os.getenv("DISPATCHER_URL", "http://127.0.0.1:8000")
        for _ in range(30):
            try:
                r = httpx.get(f"{url}/estado", timeout=1.0)
                if r.status_code == 200 and r.json()["replicas_viva"] == NUM_REPLICAS:
                    break
            except Exception:
                pass
            time.sleep(0.5)

        print(f"[dev] réplicas + dispatcher listos en {url} (pids en .live_pids.txt)")
        print("[dev] Ctrl+C para detener…", flush=True)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
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
        try:
            pids_file.unlink(missing_ok=True)
        except Exception:
            pass
        print("[dev] pila detenida")
    return 0


if __name__ == "__main__":
    sys.exit(main())
"""Inyector de fallas.

Mata una réplica concreta (CRASH) y registra el timestamp de inyección como
punto de referencia para la métrica de detección.

Uso:
  python backend/injector/injector.py B [--log results/injection_e1.log]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import httpx  # noqa: E402


def _find_replica(rid: str, dispatcher_url: str) -> str:
    r = httpx.get(f"{dispatcher_url}/estado", timeout=3.0)
    r.raise_for_status()
    replicas = r.json().get("replicas", [])
    for rep in replicas:
        if rep["id"].upper() == rid.upper():
            return rep["url"]
    raise SystemExit(f"Réplica {rid} no registrada en el dispatcher")


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="RECAUDO-T inyector de fallas")
    ap.add_argument("replica", help="Réplica a matar (A, B, C…)")
    ap.add_argument("--log", default="results/injection_e1.log")
    ap.add_argument("--dispatcher", default="http://127.0.0.1:8000")
    args = ap.parse_args()

    t_inyeccion = time.time()
    url = _find_replica(args.replica.upper(), args.dispatcher)

    Path(args.log).parent.mkdir(parents=True, exist_ok=True)
    line = f"[{t_inyeccion:.3f}] INJECTOR CRASH {args.replica.upper()}"
    with open(args.log, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(line, flush=True)

    try:
        httpx.post(f"{url}/chaos/crash", timeout=3.0)
    except Exception:
        pass  # el crash corta la conexión de forma esperada
    print(f"Crash ejecutado sobre {args.replica.upper()} ({url})", flush=True)


if __name__ == "__main__":
    main()
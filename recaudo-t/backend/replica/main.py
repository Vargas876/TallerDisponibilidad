"""RECAUDO-T — Réplica de consulta de saldo.

Proceso independiente que expone el contrato del taller:
  GET  /ping                → comprobación de vida (Ping/Echo)
  GET  /saldo/{id_tarjeta}  → saldo determinístico por tarjeta
  POST /chaos/crash         → suicidio del proceso (inyección de falla)

Ejemplo:
  python backend/replica/main.py            # REPLICA_ID=A REPLICA_PORT=8001
  REPLICA_ID=B REPLICA_PORT=8002 python backend/replica/main.py
"""
import asyncio
import hashlib
import os
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI, HTTPException  # noqa: E402

from backend.replica.config import replica_settings  # noqa: E402

_SETTINGS = replica_settings()
REPLICA_ID: str = _SETTINGS["replica_id"]
_LATENCY_RANGE = (0.0, _SETTINGS["latency_ms"] / 1000.0)
_BROKEN_SALDO: bool = bool(_SETTINGS["broken_saldo"])

app = FastAPI(title=f"RECAUDO-T Réplica {REPLICA_ID}", version="1.0.0")


def _saldo(tarjeta: str) -> int:
    """Saldo determinístico: mismo tarjeta + réplica → mismo resultado."""
    digest = hashlib.sha256(f"{REPLICA_ID}:{tarjeta}".encode()).hexdigest()
    return 5_000 + int(digest[:8], 16) % 25_000


@app.get("/ping")
async def ping():
    return {"replica_id": REPLICA_ID}


@app.get("/saldo/{id_tarjeta}")
async def saldo(id_tarjeta: str):
    if _LATENCY_RANGE[1] > 0:
        await asyncio.sleep(random.uniform(*_LATENCY_RANGE))
    if _BROKEN_SALDO:
        raise HTTPException(status_code=500, detail="fallo inducido en /saldo (Q3)")
    return {"replica_id": REPLICA_ID, "tarjeta": id_tarjeta, "saldo": _saldo(id_tarjeta)}


@app.post("/chaos/crash")
async def crash():
    """Termina el proceso de forma inmediata. El timestamp lo registra el inyector."""
    print(f"[{time.time():.3f}] RÉPLICA {REPLICA_ID} — CRASH INDUCIDO", flush=True)
    os._exit(137)


if __name__ == "__main__":
    import uvicorn

    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    uvicorn.run(app, host=_SETTINGS["host"], port=_SETTINGS["port"], log_level="info")
"""Cliente de carga en vivo como web service de Render.

La API de Render no permite `background_worker` en plan free, así que el
cliente corre como web service: sirve `/healthz` (Render lo sondea y eso lo
mantiene despierto) y, en segundo plano, ejecuta el bucle continuo de carga
del client.py contra el dispatcher desplegado.

Envs: CLIENT_DISPATCHER_URL, CLIENT_RATE (default 20), REQUEST_TIMEOUT, PORT.
"""
from __future__ import annotations

import asyncio
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import uvicorn  # noqa: E402
from fastapi import FastAPI  # noqa: E402

from backend.client.client import main_async  # noqa: E402

RATE = int(os.getenv("CLIENT_RATE", "20"))
URL = os.getenv("CLIENT_DISPATCHER_URL", os.getenv("DISPATCHER_URL", "http://127.0.0.1:8000"))
TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "0.8"))
PORT = int(os.getenv("PORT", "8000"))


@asynccontextmanager
async def _lifespan(app):
    task = asyncio.create_task(
        main_async(out="", duration=0, rate=RATE, url=URL, timeout=TIMEOUT, loop=True)
    )
    yield
    task.cancel()


app = FastAPI(title="RECAUDO-T cliente en vivo", lifespan=_lifespan)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
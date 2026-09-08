"""Redundancia activa: consulta paralela a las réplicas VIVA.

Se lanza una petición a cada réplica saludable y se devuelve la PRIMERA
respuesta válida (HTTP 200 + saldo). Las restantes se cancelan. Esto hace que
el cliente prácticamente no perciba la caída de una réplica: el dispatcher
sigue consultando a las que siguen vivas desde el primer instante.
"""
from __future__ import annotations

import asyncio
import time

import httpx
from fastapi import HTTPException

from backend.dispatcher.state import StateStore


async def _probe_one(r, tarjeta: str, client: httpx.AsyncClient, timeout: float):
    t0 = time.perf_counter()
    try:
        resp = await client.get(f"{r.url}/saldo/{tarjeta}", timeout=timeout)
    except Exception:
        r.total_requests += 1
        r.failed_requests += 1
        raise
    r.total_requests += 1
    if resp.status_code == 200:
        r.successful_requests += 1
        return r, resp.json()
    r.failed_requests += 1
    raise RuntimeError(f"HTTP {resp.status_code}")


async def dispatch_saldo(tarjeta: str, store: StateStore, client: httpx.AsyncClient, timeout: float) -> dict:
    targets = store.viva()
    if not targets:
        raise HTTPException(status_code=503, detail="sin réplicas disponibles")
    store.total_solicitudes += 1

    tasks = {asyncio.create_task(_probe_one(r, tarjeta, client, timeout)): r for r in targets}
    pending: set = set(tasks)

    while pending:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            try:
                _r, payload = task.result()
            except Exception:
                continue
            for rest in pending:
                rest.cancel()
            payload["atendida_por"] = _r.id
            return payload
    raise HTTPException(status_code=503, detail="ninguna réplica respondió")
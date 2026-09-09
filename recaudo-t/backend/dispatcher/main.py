"""RECAUDO-T — Dispatcher (Ping/Echo + Redundancia Activa).

Exposición pública:
  GET  /saldo/{id_tarjeta}   → redundancia activa (primera respuesta válida)
  GET  /estado               → snapshot del estado interno
  GET  /health               → healthcheck
  WS   /ws                   → eventos + snapshot en tiempo real
  POST /chaos/crash/{id}     → inyecta CRASH en una réplica (E1)
  POST /chaos/broken/{id}    → toggle saldo roto en una réplica (Q3)

Ejemplo:
  python backend/dispatcher/main.py
"""
import asyncio
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import httpx  # noqa: E402
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from backend.dispatcher import state as st  # noqa: E402
from backend.dispatcher.config import dispatcher_settings  # noqa: E402
from backend.dispatcher.monitor import MonitorLog, PingEchoMonitor  # noqa: E402
from backend.dispatcher.redundancy import dispatch_saldo  # noqa: E402
from backend.dispatcher.websocket import ConnectionManager, broadcaster  # noqa: E402

SET = dispatcher_settings()

log = MonitorLog(SET["monitor_log"])
manager = ConnectionManager()
events: asyncio.Queue = asyncio.Queue()

store: st.StateStore | None = None
http: httpx.AsyncClient | None = None


class BrokenRequest(BaseModel):
    activo: bool


def on_transition(replica, old_status: str, note: str) -> None:
    log.write(f"REPLICA_{replica.id} {old_status} → {replica.status} ({note})")
    events.put_nowait(
        {
            "type": "replica_status_changed",
            "replica": replica.id,
            "old": old_status,
            "status": replica.status,
            "ts": time.time(),
        }
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    global store, http
    http = httpx.AsyncClient(timeout=SET["request_timeout"])
    store = st.StateStore(
        SET["replicas"],
        on_transition,
        failure_threshold=SET["failure_threshold"],
        recovery_threshold=SET["recovery_threshold"],
    )
    log.write(
        f"DISPATCHER ARRANCA — réplicas={', '.join(f'{rid}:{url}' for rid, url in SET['replicas'].items())}"
    )
    monitor = PingEchoMonitor(store, http, SET, log)
    app.state.monitor_task = asyncio.create_task(monitor.run())
    app.state.broadcaster = asyncio.create_task(broadcaster(manager, store, events))
    yield
    app.state.monitor_task.cancel()
    app.state.broadcaster.cancel()
    await asyncio.gather(app.state.monitor_task, app.state.broadcaster, return_exceptions=True)
    await http.aclose()


app = FastAPI(title="RECAUDO-T Dispatcher", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in SET["cors_origins"].split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _replica_url(target: str) -> tuple[str, str] | None:
    rid = target.upper()
    for id_, url in SET["replicas"].items():
        if id_.upper() == rid:
            return id_, url
    return None


@app.post("/chaos/crash/{target}")
async def chaos_crash(target: str):
    """Escenario E1: induce CRASH en una réplica (la mata al instante)."""
    global http
    hit = _replica_url(target)
    if not hit:
        raise HTTPException(400, f"réplica {target} no registrada")
    _, url = hit
    store.get(target.upper()).saldo_roto = False  # la réplica renace limpia
    log.write(f"CAOS E1: CRASH inducido sobre {target.upper()} ({url})")
    events.put_nowait({"type": "chaos", "accion": "crash", "replica": target.upper(), "ts": time.time()})
    try:
        await http.post(f"{url}/chaos/crash", timeout=3.0)
    except httpx.HTTPError:
        pass  # el proceso muere y corta la conexión — esperado
    return {"ok": True, "accion": "crash", "replica": target.upper()}


@app.post("/chaos/broken/{target}")
async def chaos_broken(target: str, req: BrokenRequest):
    """Escenario Q3: activa/desactiva saldo roto en una réplica (ping OK, /saldo 500)."""
    global http
    hit = _replica_url(target)
    if not hit:
        raise HTTPException(400, f"réplica {target} no registrada")
    _, url = hit
    try:
        r = await http.post(f"{url}/chaos/broken", json={"activo": req.activo}, timeout=3.0)
        r.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(502, f"réplica {target} no respondió a /chaos/broken: {e}")
    store.get(target.upper()).saldo_roto = req.activo
    log.write(f"CAOS Q3: saldo roto={'ON' if req.activo else 'OFF'} sobre {target.upper()} ({url})")
    events.put_nowait(
        {"type": "chaos", "accion": "broken", "activo": req.activo, "replica": target.upper(), "ts": time.time()}
    )
    return {"ok": True, "accion": "broken", "activo": req.activo, "replica": target.upper()}


@app.get("/health")
async def health():
    return {"estado": "ok", "ts": time.time()}


@app.get("/estado")
async def estado():
    global store
    return st.snapshot(store)


@app.get("/saldo/{id_tarjeta}")
async def saldo(id_tarjeta: str):
    global store, http
    if store is None or http is None:
        raise HTTPException(503, "dispatcher inicializando")
    return await dispatch_saldo(id_tarjeta, store, http, SET["request_timeout"])


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        await ws.send_json({"type": "hello", "ts": time.time(), **st.snapshot(store)})
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)


if __name__ == "__main__":
    import uvicorn

    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    uvicorn.run(app, host=SET["host"], port=SET["port"], log_level="info")
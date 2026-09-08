"""RECAUDO-T — Dispatcher (Ping/Echo + Redundancia Activa).

Exposición pública:
  GET  /saldo/{id_tarjeta}   → redundancia activa (primera respuesta válida)
  GET  /estado               → snapshot del estado interno
  GET  /health               → healthcheck
  WS   /ws                   → eventos + snapshot en tiempo real

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
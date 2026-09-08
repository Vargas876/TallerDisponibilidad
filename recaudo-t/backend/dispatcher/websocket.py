"""Fantasma WebSocket: broadcast a los clientes del dashboard."""
from __future__ import annotations

import asyncio

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, message: dict) -> None:
        if not self.active:
            return
        dead = []
        for ws in list(self.active):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


async def broadcaster(manager: ConnectionManager, store, events: asyncio.Queue) -> None:
    """Enviar snapshot periódico + eventos de transición al instante."""
    from backend.dispatcher.state import snapshot

    while True:
        await asyncio.sleep(1.0)
        try:
            await manager.broadcast({"type": "snapshot", **snapshot(store)})
        except Exception:
            pass
        while not events.empty():
            ev = events.get_nowait()
            try:
                await manager.broadcast(ev)
            except Exception:
                pass
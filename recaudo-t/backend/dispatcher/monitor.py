"""Monitor Ping/Echo + bitácora de vuelo (logs/monitor.log).

Cada PING_INTERVAL segundos sondea /ping de todas las réplicas con un
timeout de PING_TIMEOUT. Acumula fallos (k = FAILURE_THRESHOLD) y éxitos
consecutivos, y dispara las transiciones VIVA → CAÍDA → VIVA.
"""
from __future__ import annotations

import asyncio
import time
from pathlib import Path

import httpx

from backend.dispatcher.state import StateStore


class MonitorLog:
    """Bitácora de vuelo en formato [epoch] evento. Es la evidencia primaria."""

    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, text: str) -> None:
        line = f"[{time.time():.3f}] {text}"
        print(line, flush=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


class PingEchoMonitor:
    def __init__(self, store: StateStore, client: httpx.AsyncClient, settings: dict, log: MonitorLog):
        self.store = store
        self.client = client
        self.interval = settings["ping_interval"]
        self.timeout = settings["ping_timeout"]
        self.log = log

    async def run(self) -> None:
        self.log.write(
            f"MONITOR INICIADO — T={self.interval}s t={self.timeout}s "
            f"k={self.store.failure_threshold} réplicas={list(self.store.all())}"
        )
        while True:
            t0 = asyncio.get_event_loop().time()
            await self.cycle()
            elapsed = asyncio.get_event_loop().time() - t0
            await asyncio.sleep(max(0.0, self.interval - elapsed))

    async def cycle(self) -> None:
        await asyncio.gather(*(self.probe(r) for r in self.store.all()), return_exceptions=True)

    async def probe(self, r) -> None:
        t0 = time.perf_counter()
        try:
            resp = await self.client.get(f"{r.url}/ping", timeout=self.timeout)
            latency_ms = (time.perf_counter() - t0) * 1000.0
            if resp.status_code == 200:
                self.log.write(f"PING {r.id} OK {latency_ms:.0f}ms")
                try:
                    self.store.mark_success(r.id, latency_ms)
                except Exception as state_err:
                    self.log.write(f"MONITOR ERROR en state: {state_err!r}")
                return
            self.log.write(f"PING {r.id} ERROR HTTP {resp.status_code}")
            self.store.mark_failure(r.id, f"HTTP {resp.status_code}")
        except Exception as exc:  # timeout / conexión rechazada
            self.log.write(f"PING {r.id} TIMEOUT ({type(exc).__name__})")
            try:
                self.store.mark_failure(r.id, type(exc).__name__)
            except Exception as state_err:
                self.log.write(f"MONITOR ERROR en state: {state_err!r}")
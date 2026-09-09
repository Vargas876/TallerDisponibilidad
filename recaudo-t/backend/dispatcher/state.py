"""Registro central de estado de réplicas (ReplicaState) y transiciones."""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Callable

VIVA = "VIVA"
CAIDA = "CAIDA"

# notas de transición para el timeline
DOWN_NOTE = "marcada CAÍDA tras N fallos consecutivos"
UP_NOTE = "recuperada tras N éxitos consecutivos"


@dataclass
class ReplicaState:
    id: str
    url: str
    status: str = VIVA
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_ping: float | None = field(default=None)
    latency_ms: float | None = field(default=None)
    last_ok: float | None = field(default=None)
    last_down: float | None = field(default=None)
    last_up: float | None = field(default=None)
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    last_error: str | None = field(default=None)
    saldo_roto: bool = False

    def snapshot(self) -> dict:
        base = asdict(self)
        base["disponible"] = self.status == VIVA
        return base


class StateStore:
    """Conjunto de réplicas + contadores globales. Evento de transición → callback."""

    def __init__(
        self,
        replicas: dict[str, str],
        on_transition: Callable[[ReplicaState, str, str], None],
        failure_threshold: int = 2,
        recovery_threshold: int = 2,
    ):
        self._replicas = {
            rid: ReplicaState(id=rid, url=url) for rid, url in replicas.items()
        }
        self._on_transition = on_transition
        self.failure_threshold = failure_threshold
        self.recovery_threshold = recovery_threshold
        self.total_solicitudes = 0
        self.start_time = time.time()
        self.last_detection: dict | None = None

    def all(self) -> list[ReplicaState]:
        return list(self._replicas.values())

    def get(self, rid: str) -> ReplicaState:
        return self._replicas[rid]

    def viva(self) -> list[ReplicaState]:
        return [r for r in self.all() if r.status == VIVA]

    def disponible(self) -> bool:
        return len(self.viva()) > 0

    def count(self) -> int:
        return sum(1 for r in self.all() if r.status == VIVA)

    # ---- transiciones del monitor ----
    def _signal(self, replica: ReplicaState, new_status: str, note: str):
        old = replica.status
        replica.status = new_status
        if self._on_transition:
            self._on_transition(replica, old, note)

    def mark_failure(self, rid: str, error: str) -> bool:
        """Registra un timeout/error. Devuelve True si se produjo una transición."""
        r = self.get(rid)
        r.last_error = error
        r.consecutive_successes = 0
        r.consecutive_failures += 1
        if r.status == VIVA and r.consecutive_failures >= self.failure_threshold:
            r.last_down = time.time()
            self.last_detection = {"replica": rid, "at": time.time()}
            self._signal(r, CAIDA, DOWN_NOTE.replace("N", str(r.consecutive_failures)))
            return True
        return False

    def mark_success(self, rid: str, latency_ms: float) -> bool:
        """Registra un ping OK. Devuelve True si se produjo una transición."""
        r = self.get(rid)
        r.last_error = None
        r.consecutive_failures = 0
        r.consecutive_successes += 1
        r.last_ping = time.time()
        r.latency_ms = round(latency_ms, 1)
        if r.status == CAIDA and r.consecutive_successes >= self.recovery_threshold:
            r.last_up = time.time()
            r.consecutive_successes = 0
            self._signal(r, VIVA, UP_NOTE.replace("N", str(self.recovery_threshold)))
            return True
        return False


def snapshot(store) -> dict:
    return {
        "version": "RECAUDO-T/1.0",
        "disponible": store.disponible(),
        "replicas_viva": store.count(),
        "replicas": [r.snapshot() for r in store.all()],
        "total_solicitudes": store.total_solicitudes,
        "last_detection": store.last_detection,
        "uptime_s": round(time.time() - store.start_time, 1),
    }
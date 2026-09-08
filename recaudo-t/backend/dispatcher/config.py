"""Configuración del dispatcher. Lee config/.env + variables de entorno."""
import os
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_ROOT / "config" / ".env")

REPLICA_PREFIX = "REPLICA_"
REPLICA_URL_SUFFIX = "_URL"


def _float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


def _int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def replicas_from_env() -> dict[str, str]:
    """Descubre réplicas desde las variables REPLICA_<ID>_URL.
    Agregar una réplica nueva NO requiere tocar código."""
    found = {}
    for key, value in os.environ.items():
        if value and key.startswith(REPLICA_PREFIX) and key.endswith(REPLICA_URL_SUFFIX):
            rid = key[len(REPLICA_PREFIX) : -len(REPLICA_URL_SUFFIX)].upper()
            found[rid] = value
    if not found:
        raise RuntimeError(
            "No se encontraron réplicas. Define REPLICA_<ID>_URL (ver config/.env)."
        )
    return {rid: found[rid] for rid in sorted(found)}


def dispatcher_settings():
    return {
        "host": os.getenv("DISPATCHER_HOST", "127.0.0.1"),
        "port": _int("DISPATCHER_PORT", 8000),
        # monitor Ping/Echo
        "ping_interval": _float("PING_INTERVAL", 1.0),
        "ping_timeout": _float("PING_TIMEOUT", 0.3),
        "failure_threshold": _int("FAILURE_THRESHOLD", 2),
        "recovery_threshold": _int("RECOVERY_THRESHOLD", 2),
        # tiempo límite para la respuesta al cliente (redundancia activa)
        "request_timeout": _float("REQUEST_TIMEOUT", 0.8),
        # registro
        "monitor_log": os.getenv("MONITOR_LOG", "logs/monitor.log"),
        # réplicas
        "replicas": replicas_from_env(),
    }
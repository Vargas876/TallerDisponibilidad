"""Configuración de una réplica. Lee config/.env y variables de entorno."""
import os
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_ROOT / "config" / ".env")


def replica_settings():
    return {
        "replica_id": os.getenv("REPLICA_ID", "A").upper(),
        "port": int(os.getenv("REPLICA_PORT", "8001")),
        "host": os.getenv("REPLICA_HOST", "127.0.0.1"),
        # latencia artificial para ejercitar la redundancia activa
        "latency_ms": float(os.getenv("REPLICA_LATENCY_MS", "0")),
        # Q3: romper /saldo pero mantener /ping OK (limitación del Ping/Echo)
        "broken_saldo": int(os.getenv("REPLICA_BROKEN_SALDO", "0")),
    }
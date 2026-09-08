"""Cliente de carga.

Genera CLIENT_RATE solicitudes por segundo durante EXPERIMENT_DURATION
segundos hacia el dispatcher y registra cada una en un CSV (evidencia E0/E1).

Columnas: timestamp_envio, timestamp_respuesta, exito, replica, tarjeta, latency_ms
A los timestamps están en segundos epoch (precisión para las métricas).

Uso:
  python backend/client/client.py [--out results/e1.csv] [--duration 40] [--rate 20]
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import httpx  # noqa: E402

_TARJETAS = [f"{random.randint(1000, 9999)}" for _ in range(64)]


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


async def main_async(out: str, duration: int, rate: int, url: str, timeout: float):
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    tasks: list[asyncio.Task] = []
    deadline = time.time() + duration
    sent = 0

    async with httpx.AsyncClient(timeout=timeout) as client:
        while time.time() < deadline - 0.25:
            lote = [
                asyncio.create_task(_request(client, url, _tarjeta(), time.time()))
                for _ in range(rate)
            ]
            tasks.extend(lote)
            sent += rate
            await asyncio.sleep(1.0)

        filas = await asyncio.gather(*tasks, return_exceptions=True)
        rows = [f for f in filas if isinstance(f, dict)]
        with open(out, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(
                fh,
                fieldnames=["timestamp_envio", "timestamp_respuesta", "exito", "replica", "tarjeta", "latency_ms"],
            )
            w.writeheader()
            for r in rows:
                w.writerow(r)

    exitos = sum(1 for r in rows if r["exito"])
    print(
        f"CLIENTE FIN: total={len(rows)} exitosos={exitos} "
        f"tasa={len(rows) / max(duration, 1):.2f} req/s -> {out}",
        flush=True,
    )


def _tarjeta() -> str:
    return _TARJETAS[int(time.time() * 100) % len(_TARJETAS)]


async def _request(client, url: str, tarjeta: str, t_envio: float) -> dict:
    t0 = time.perf_counter()
    try:
        resp = await client.get(f"{url}/saldo/{tarjeta}")
        t_resp = time.time()
        if resp.status_code == 200:
            data = resp.json()
            return {
                "timestamp_envio": f"{t_envio:.3f}",
                "timestamp_respuesta": f"{t_resp:.3f}",
                "exito": 1,
                "replica": data.get("atendida_por", "-"),
                "tarjeta": tarjeta,
                "latency_ms": f"{(time.perf_counter() - t0) * 1000:.2f}",
            }
        return {
            "timestamp_envio": f"{t_envio:.3f}",
            "timestamp_respuesta": f"{t_resp:.3f}",
            "exito": 0,
            "replica": "-",
            "tarjeta": tarjeta,
            "latency_ms": f"{(time.perf_counter() - t0) * 1000:.2f}",
        }
    except Exception:
        return {
            "timestamp_envio": f"{t_envio:.3f}",
            "timestamp_respuesta": f"{time.time():.3f}",
            "exito": 0,
            "replica": "-",
            "tarjeta": tarjeta,
            "latency_ms": "",
        }


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="RECAUDO-T cliente de carga")
    ap.add_argument("--out", default=os.getenv("CLIENT_OUT", "results/e1.csv"))
    ap.add_argument("--duration", type=int, default=_env_int("EXPERIMENT_DURATION", 40))
    ap.add_argument("--rate", type=int, default=_env_int("CLIENT_RATE", 20))
    ap.add_argument("--url", default=os.getenv("DISPATCHER_URL", "http://127.0.0.1:8000"))
    ap.add_argument("--timeout", type=float, default=float(os.getenv("REQUEST_TIMEOUT", "0.8")))
    args = ap.parse_args()
    try:
        asyncio.run(main_async(args.out, args.duration, args.rate, args.url, args.timeout))
    except BaseException:
        Path("client.err").write_text(
            "".join(__import__("traceback").format_exc()), encoding="utf-8"
        )
        raise


if __name__ == "__main__":
    main()
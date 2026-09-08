"""Cálculo automático de métricas a partir de las evidencias.

Recibe el CSV de un experimento + la bitácora del monitor + el archivo de
inyección y produce results/metrics.json (y un reporte en consola).

Uso:
  python backend/metrics.py --experiment e1 --csv results/e1.csv \
      --injection results/injection_e1.log                # detección solo en e1
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv  # noqa: E402

_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_ROOT / "config" / ".env")

MONITOR_LOG = os.getenv("MONITOR_LOG", "logs/monitor.log")
RESULTS_DIR = Path(os.getenv("RESULTS_DIR", "results"))
TRANSICION_A_CAIDA = re.compile(r"\[(\d+\.\d+)\]\s*REPLICA_([A-Z]+)\s+VIVA\s+→\s+CAI?DA")
TRANSICION_A_VIVA = re.compile(r"\[(\d+\.\d+)\]\s*REPLICA_([A-Z]+)\s+CAI?DA\s+→\s+VIVA")
INYECCION = re.compile(r"\[(\d+\.\d+)\]\s*INJECTOR\s+CRASH\s+([A-Z]+)")


def _leer_csv(buscar: Path):
    if not buscar.exists():
        return None
    rows = []
    with buscar.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append(row)
    return rows


def computar(experiment: str, csv_path: Path, injection_path: Path | None):
    carga = _leer_csv(csv_path)
    if carga is None:
        raise SystemExit(f"CSV no encontrado: {csv_path}")

    total = len(carga)
    exitosos = sum(1 for r in carga if int(r.get("exito", 0)) == 1)
    fallidos = total - exitosos
    success_rate = round(100.0 * exitosos / total, 4) if total else 0.0

    # distribución por réplica
    distribucion: dict[str, int] = {}
    for r in carga:
        rep = r.get("replica", "-")
        distribucion[rep] = distribucion.get(rep, 0) + 1

    # serie por segundo (éxitos / fallos) en segundos relativos al experimento
    serie: dict[int, dict] = {}
    for r in carga:
        try:
            seg_abs = int(float(r["timestamp_envio"]))
        except (KeyError, ValueError):
            continue
        punto = serie.setdefault(seg_abs, {"ok": 0, "fail": 0})
        punto["ok" if int(r.get("exito", 0)) == 1 else "fail"] += 1
    t0 = min(serie) if serie else 0
    serie_lista = [{"seg": s - t0, **v} for s, v in sorted(serie.items())]

    # latencias (resumen)
    lat_vals = [float(r["latency_ms"]) for r in carga if r.get("latency_ms")]
    lat_mean = round(sum(lat_vals) / len(lat_vals), 2) if lat_vals else None

    metricas = {
        "experiment": experiment,
        "fecha": os.path.getmtime(csv_path),
        "total_requests": total,
        "successful_requests": exitosos,
        "failed_requests": fallidos,
        "success_rate": success_rate,
        "latency_mean_ms": lat_mean,
        "distribucion_por_replica": distribucion,
        "serie_por_segundo": serie_lista,
    }

    # solo e1 / experiments con inyección
    if injection_path and injection_path.exists():
        texto = injection_path.read_text(encoding="utf-8")
        m_iny = None
        for m in INYECCION.finditer(texto):
            m_iny = m  # último match = corrida más reciente
        if m_iny:
            t_iny = float(m_iny.group(1))
            target = m_iny.group(2)
            metricas["inyeccion"] = {"ts": t_iny, "replica": target}
            log_txt = Path(MONITOR_LOG).read_text(encoding="utf-8")
            m_det = None
            for m in TRANSICION_A_CAIDA.finditer(log_txt):
                if m.group(2) == target:
                    m_det = m  # último match = corrida más reciente
            if m_det:
                t_det = float(m_det.group(1))
                metricas["deteccion"] = {
                    "ts": t_det,
                    "tiempo_s": round(t_det - t_iny, 3),
                    "replica": m_det.group(2),
                }
            m_rec = None
            for m in TRANSICION_A_VIVA.finditer(log_txt):
                if m.group(2) == target:
                    m_rec = m
            if m_rec:
                t_rec = float(m_rec.group(1))
                metricas["recuperacion"] = {
                    "ts": t_rec,
                    "replica": m_rec.group(2),
                }
                if m_det:
                    metricas["recuperacion"]["tiempo_s"] = round(t_rec - t_det, 3)

    (RESULTS_DIR / "metrics.json").write_text(
        json.dumps(metricas, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return metricas


def _reporte(m: dict):
    det = m.get("deteccion", {}).get("tiempo_s")
    print("=" * 50)
    print(f"EXPERIMENTO {m['experiment'].upper()}")
    print("=" * 50)
    print(f"  Solicitudes        {m['total_requests']}")
    print(f"  Exitosas           {m['successful_requests']}")
    print(f"  Fallidas           {m['failed_requests']}")
    print(f"  Tasa de éxito      {m['success_rate']}%")
    print(f"  Latencia media     {m['latency_mean_ms']} ms")
    print(f"  Distribución       {m['distribucion_por_replica']}")
    if det is not None:
        print(f"  DETECCIÓN          {det} s")
    if "recuperacion" in m:
        print(f"  Recuperación ts    {m['recuperacion']['ts']}")
    print("=" * 50)


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="RECAUDO-T métricas")
    ap.add_argument("--experiment", default="e1")
    ap.add_argument("--csv", default="results/e1.csv")
    ap.add_argument("--injection", default="results/injection_e1.log")
    args = ap.parse_args()
    m = computar(args.experiment, Path(args.csv), Path(args.injection))
    _reporte(m)


if __name__ == "__main__":
    main()
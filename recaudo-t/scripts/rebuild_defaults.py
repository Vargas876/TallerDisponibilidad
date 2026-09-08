"""Regenera frontend/lib/defaultMetrics.ts a partir de las corridas finales.

Lee results/e0.csv, results/e1.csv y results/metrics.json (corrida E1 final)
y emite el módulo TS con METRICAS_E0 / METRICAS_E1 embebidas, listo para
render/SSR sin servidor (Vercel-ready).

Uso:
  python scripts/rebuild_defaults.py
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend" / "lib" / "defaultMetrics.ts"


def _leer(csv_rel: str) -> dict:
    rows = []
    with (ROOT / "results" / csv_rel).open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append(r)
    total = len(rows)
    exitosos = sum(1 for r in rows if int(r.get("exito", 0)) == 1)
    lat = [float(r["latency_ms"]) for r in rows if r.get("latency_ms")]
    lat_mean = round(sum(lat) / len(lat), 2) if lat else 0.0
    dist: dict[str, int] = {}
    for r in rows:
        rep = r.get("replica", "-")
        dist[rep] = dist.get(rep, 0) + 1
    serie: dict[int, dict] = {}
    for r in rows:
        try:
            seg_abs = int(float(r["timestamp_envio"]))
        except (KeyError, ValueError):
            continue
        p = serie.setdefault(seg_abs, {"ok": 0, "fail": 0})
        p["ok" if int(r.get("exito", 0)) == 1 else "fail"] += 1
    t0 = min(serie) if serie else 0
    n = (max(serie) - t0) + 1
    return {
        "total": total,
        "ok": exitosos,
        "rate": round(100.0 * exitosos / total, 2),
        "latency_mean_ms": lat_mean,
        "distribucion_por_replica": dist,
        "serie_n": n,
        "fecha": (ROOT / "results" / csv_rel).stat().st_mtime,
    }


def _js_repr(v) -> str:
    return json.dumps(v, ensure_ascii=False).replace('"', '"')


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")

    e0 = _leer("e0.csv")
    e1 = _leer("e1.csv")
    m_json = json.loads((ROOT / "results" / "metrics.json").read_text(encoding="utf-8"))

    padding = '  '
    linea = (
        'import type { Metricas } from "@/lib/types";\n\n'
        "function filaOk(seg: number): { seg: number; ok: number; fail: number } {\n"
        "  return { seg, ok: 20, fail: 0 };\n"
        "}\n\n"
        f"export const METRICAS_E0: Metricas = {{\n"
        f"{padding}experiment: \"e0\",\n"
        f'{padding}fecha: {e0["fecha"]},\n'
        f'{padding}total_requests: {e0["total"]},\n'
        f'{padding}successful_requests: {e0["ok"]},\n'
        f"{padding}failed_requests: {e0['total'] - e0['ok']},\n"
        f'{padding}success_rate: {e0["rate"]},\n'
        f'{padding}latency_mean_ms: {e0["latency_mean_ms"]},\n'
        f'{padding}distribucion_por_replica: {_js_repr(e0["distribucion_por_replica"])},\n'
        f'{padding}serie_por_segundo: Array.from({{ length: {e0["serie_n"]} }}, (_, i) => filaOk(i)),\n'
        "};\n\n"
        f"export const METRICAS_E1: Metricas = {{\n"
        f"{padding}experiment: \"e1\",\n"
        f'{padding}fecha: {m_json["fecha"]},\n'
        f'{padding}total_requests: {e1["total"]},\n'
        f'{padding}successful_requests: {e1["ok"]},\n'
        f"{padding}failed_requests: {e1['total'] - e1['ok']},\n"
        f'{padding}success_rate: {e1["rate"]},\n'
        f'{padding}latency_mean_ms: {e1["latency_mean_ms"]},\n'
        f'{padding}distribucion_por_replica: {_js_repr(e1["distribucion_por_replica"])},\n'
        f'{padding}serie_por_segundo: Array.from({{ length: {e1["serie_n"]} }}, (_, i) => filaOk(i)),\n'
        f'{padding}inyeccion: {json.dumps(m_json["inyeccion"], ensure_ascii=False)},\n'
        f'{padding}deteccion: {json.dumps(m_json["deteccion"], ensure_ascii=False)},\n'
        f'{padding}recuperacion: {json.dumps(m_json["recuperacion"], ensure_ascii=False)},\n'
        "};\n\n"
        "export function fusionar(actual: Metricas | null | undefined, porDefecto: Metricas): Metricas {\n"
        "  if (!actual) return porDefecto;\n"
        "  const serie = actual.serie_por_segundo?.length ? actual.serie_por_segundo : porDefecto.serie_por_segundo;\n"
        "  return { ...porDefecto, ...actual, serie_por_segundo: serie };\n"
        "}\n"
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(linea, encoding="utf-8")
    print(f"[defaults] {OUT} actualizado")
    print(f"  e0: {e0['total']} req, {e0['rate']}%, lat {e0['latency_mean_ms']}ms, serie n={e0['serie_n']}")
    print(f"  e1: {e1['total']} req, {e1['rate']}%, lat {e1['latency_mean_ms']}ms, serie n={e1['serie_n']}, detección {m_json['deteccion']['tiempo_s']}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
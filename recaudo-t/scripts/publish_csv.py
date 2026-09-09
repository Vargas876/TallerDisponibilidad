"""Publica las evidencias CSV/logs en frontend/public/csv para servirlas desde Vercel.

Copia results/e0.csv, results/e1.csv, results/q3.csv y los logs de inyección
a frontend/public/csv/. Se ejecuta antes de desplegar el frontend o a mano:
  python scripts/publish_csv.py
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "frontend" / "public" / "csv"

FUENTES = [
    "results/e0.csv",
    "results/e1.csv",
    "results/q3.csv",
    "results/injection_e1.log",
    "results/injection_live.log",
]


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    copiados = 0
    faltantes = 0
    for rel in FUENTES:
        origen = ROOT / rel
        if not origen.exists():
            print(f"  [skip] faltante: {rel}", flush=True)
            faltantes += 1
            continue
        shutil.copy2(origen, DEST / origen.name)
        print(f"  [copy] {rel} -> frontend/public/csv/{origen.name}", flush=True)
        copiados += 1
    print(f"publicados={copiados} faltantes={faltantes}", flush=True)
    return 0 if copiados else 1


if __name__ == "__main__":
    sys.exit(main())
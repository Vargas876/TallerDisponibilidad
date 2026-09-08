"""Escenario E1 en vivo contra el despliegue de Render.

Ejecuta una inyección real de falla (POST /chaos/crash sobre una réplica
desplegada) y mide en vivo la detección del monitor Ping/Echo y la
recuperación (Render reinicia la réplica automáticamente al morir el proceso).

Además demuestra la máscara de fallas: mientras la réplica está CAÍDA se
siguen enviando solicitudes /saldo al dispatcher y todas responden OK porque
la redundancia activa descarta la réplica muerta del fan-out.

Uso:
  python scripts/demo_live.py --target C
  python scripts/demo_live.py --target B --timeout-recover 300

Salida: results/demo_live.json y results/injection_live.log
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx  # noqa: E402

DISPO_DEFAULT = "https://recaudo-t-dispatcher.onrender.com"


def _estado(client: httpx.Client, dispatcher_url: str):
    r = client.get(f"{dispatcher_url}/estado", timeout=5.0)
    r.raise_for_status()
    return r.json()


def _saldo(client: httpx.Client, dispatcher_url: str):
    r = client.get(f"{dispatcher_url}/saldo/1111222233334444", timeout=3.0)
    return r.status_code, r.json() if r.status_code < 300 else None


def _redeploy(client: httpx.Client, token: str, service_id: str) -> str:
    r = client.post(
        f"https://api.render.com/v1/services/{service_id}/deploys",
        headers={"Authorization": f"Bearer {token}"},
        json={},
        timeout=15.0,
    )
    r.raise_for_status()
    data = r.json()
    return data["deploy"]["id"] if isinstance(data, dict) and "deploy" in data else data["id"]


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description="RECAUDO-T escenario E1 en vivo (Render)")
    ap.add_argument("--dispatcher", default=DISPO_DEFAULT)
    ap.add_argument("--target", default="C", help="Réplica a tumbar (A, B o C)")
    ap.add_argument("--service-id", help="id Render del servicio réplica (para --redeploy)")
    ap.add_argument("--redeploy", action="store_true", default=os.getenv("DEMO_REDEPLOY", "") == "1",
                    help="Recuperar vía redeploy de la API de Render (usa RENDER_TOKEN)")
    ap.add_argument("--log", default="results/injection_live.log")
    ap.add_argument("--out", default="results/demo_live.json")
    ap.add_argument("--timeout-detect", type=int, default=60)
    ap.add_argument("--timeout-recover", type=int, default=180)
    args = ap.parse_args()

    ROOT = Path(__file__).resolve().parents[1]
    target = args.target.upper()

    with httpx.Client() as client:
        est = _estado(client, args.dispatcher)
        rep = next((x for x in est["replicas"] if x["id"] == target), None)
        if rep is None:
            print(f"Réplica {target} no registrada; disponibles: {[r['id'] for r in est['replicas']]}")
            return 2
        if rep["status"] != "VIVA":
            print(f"Réplica {target} está {rep['status']} — elige una VIVA o espera.")
            return 2
        print(f"Estado inicial: {est['disponible']=} | {est['replicas_viva']=} | {target} VIVA ({rep['url']})")

        t_iny = time.time()
        Path(args.log).parent.mkdir(parents=True, exist_ok=True)
        with open(args.log, "a", encoding="utf-8") as fh:
            fh.write(f"[{t_iny:.3f}] INJECTOR CRASH {target} (LIVE)\n")
        print(f"\n[t={t_iny:.3f}] INyectando CRASH a {target} ({rep['url']})")

        # lote de control: saldos justo antes de tumbar
        pre = [_saldo(client, args.dispatcher) for _ in range(5)]
        print(f"saldos justo antes (todos deben ser 200): {[s for s, _ in pre]}")
        try:
            httpx.post(f"{rep['url']}/chaos/crash", timeout=3.0)
        except Exception:
            pass  # el crash corta la conexión de forma esperada

        # --- detección del monitor Ping/Echo ---
        t_det = None
        det_t0 = time.time()
        while time.time() - det_t0 < args.timeout_detect:
            est = _estado(client, args.dispatcher)
            r = next(x for x in est["replicas"] if x["id"] == target)
            if r["status"] == "CAIDA":
                t_det = time.time()
                break
            time.sleep(0.3)
        det_s = round(t_det - t_iny, 3) if t_det else None
        print(f"\n[det] {target} marcada CAÍDA en +{det_s}s desde la inyección"
              if t_det else f"\n[det] NO se detectó la caída en {args.timeout_detect}s")

        # --- máscara de fallas: saldos durante la caída, todos deben responder ---
        dur = 6
        t0 = time.time()
        ok = fail = 0
        while time.time() - t0 < dur:
            code, _ = _saldo(client, args.dispatcher)
            if code == 200:
                ok += 1
            else:
                fail += 1
            time.sleep(0.4)
        print(f"[mask] {dur}s de tráfico con {target} CAÍDA: {ok} OK / {fail} fallos (masking activo)")

        est = _estado(client, args.dispatcher)
        print(f"[mask] dispatcher sigue disponible={est['disponible']} replicas_viva={est['replicas_viva']}")

        # --- recuperación ---
        # Condición para emitir la recuperación: el monitor la vuelve a ver VIVA.
        def _esperar_viva(comentario: str, max_s: int) -> float | None:
            t_w = time.time()
            last_print = 0
            while time.time() - t_w < max_s:
                try:
                    est = _estado(client, args.dispatcher)
                    r = next(x for x in est["replicas"] if x["id"] == target)
                    if r["status"] == "VIVA":
                        pr = httpx.get(f"{rep['url']}/ping", timeout=2.0)
                        if pr.status_code == 200:
                            return time.time()
                except Exception:
                    pass
                time.sleep(2.0)
                e = int(time.time() - t_w)
                if e - last_print >= 15:
                    print(f"[rec] {comentario} ... {e}s", flush=True)
                    last_print = e
            return None

        t_rec = None
        rec_comentario = "esperando a que Render reinicie la réplica"
        if args.redeploy:
            token = os.getenv("RENDER_TOKEN", "")
            if token:
                did = _redeploy(client, token, args.service_id)
                rec_comentario = f"expandido redeploy {did} — reiniciando..."
            else:
                print("[rec] --redeploy sin RENDER_TOKEN; espero reinicio espontáneo")
        if t_det:
            t_rec = _esperar_viva(rec_comentario, args.timeout_recover)
        rec_s = round(t_rec - t_det, 3) if t_rec else None
        print(f"\n[rec] {target} VIVA de nuevo +{rec_s}s después de la detección"
              if t_rec else f"\n[rec] {target} no volvió en {args.timeout_recover}s — redeployea/restarta en Render (o usa --redeploy)")

        est = _estado(client, args.dispatcher)
        evidencia = {
            "escenario": "E1_vivo",
            "target": target,
            "urls": {"dispatcher": args.dispatcher, "replica": rep["url"]},
            "inyeccion": round(t_iny, 3),
            "deteccion": {"ts": round(t_det, 3), "delta_s": det_s} if t_det else None,
            "mascara_de_fallas": {"solicitudes_ok": ok, "fallos": fail, "duracion_s": dur},
            "recuperacion": {"ts": round(t_rec, 3), "delta_s_desde_deteccion": rec_s} if t_rec else None,
            "reinicio_espontaneo_sin_ventana": t_det is None,
            "notas": ("Render reinició la réplica antes de que el monitor la marcara CAÍDA "
                      "si reinicio_espontaneo_sin_ventana es true.") if t_det is None else None,
            "estado_final": {"disponible": est["disponible"], "replicas_viva": est["replicas_viva"]},
            "replica_final": next((x for x in est["replicas"] if x["id"] == target), None),
        }
        out = ROOT / args.out
        out.write_text(json.dumps(evidencia, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nEvidencia -> {out}")
        print(json.dumps(evidencia, indent=2, ensure_ascii=False))

        assert t_det, "no se detectó la caída — revisa el monitor"
        assert ok >= 1 and fail == 0, "la redundancia no enmascaró la falla"
        return 0


if __name__ == "__main__":
    sys.exit(main())
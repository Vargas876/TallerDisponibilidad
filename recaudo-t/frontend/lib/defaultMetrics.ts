import type { Metricas } from "@/lib/types";

function filaOk(seg: number): { seg: number; ok: number; fail: number } {
  return { seg, ok: 20, fail: 0 };
}

export const METRICAS_E0: Metricas = {
  experiment: "e0",
  fecha: 1788884315.964766,
  total_requests: 800,
  successful_requests: 800,
  failed_requests: 0,
  success_rate: 100.0,
  latency_mean_ms: 214.18,
  distribucion_por_replica: {"A": 320, "C": 194, "B": 286},
  serie_por_segundo: Array.from({ length: 40 }, (_, i) => filaOk(i)),
};

export const METRICAS_E1: Metricas = {
  experiment: "e1",
  fecha: 1788884363.5725183,
  total_requests: 800,
  successful_requests: 800,
  failed_requests: 0,
  success_rate: 100.0,
  latency_mean_ms: 219.41,
  distribucion_por_replica: {"A": 347, "C": 256, "B": 197},
  serie_por_segundo: Array.from({ length: 40 }, (_, i) => filaOk(i)),
  inyeccion: {"ts": 1788884337.965, "replica": "B"},
  deteccion: {"ts": 1788884340.104, "tiempo_s": 2.139, "replica": "B"},
  recuperacion: {"ts": 1788884345.867, "replica": "B", "tiempo_s": 5.763},
};

export function fusionar(actual: Metricas | null | undefined, porDefecto: Metricas): Metricas {
  if (!actual) return porDefecto;
  const serie = actual.serie_por_segundo?.length ? actual.serie_por_segundo : porDefecto.serie_por_segundo;
  return { ...porDefecto, ...actual, serie_por_segundo: serie };
}

"use client";

import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import type { Metricas } from "@/lib/types";
import { PREGUNTAS } from "@/lib/preguntas";
import { QaPanel } from "@/components/QaPanel";
import { MeasuredChart } from "@/components/MeasuredChart";
import { KpiCell } from "@/components/KpiCell";

interface Payload {
  fuente: string;
  e0: Metricas;
  e1: Metricas;
}

const PRESETS: Payload = {
  fuente: "incrustado",
  e0: {
    experiment: "e0",
    fecha: 0,
    total_requests: 0,
    successful_requests: 0,
    failed_requests: 0,
    success_rate: 0,
    latency_mean_ms: null,
    distribucion_por_replica: {},
    serie_por_segundo: [],
  },
  e1: {
    experiment: "e1",
    fecha: 0,
    total_requests: 0,
    successful_requests: 0,
    failed_requests: 0,
    success_rate: 0,
    latency_mean_ms: null,
    distribucion_por_replica: {},
    serie_por_segundo: [],
  },
};

export default function ResultadosPage() {
  const [payload, setPayload] = useState<Payload>(PRESETS);
  const [sel, setSel] = useState<"e0" | "e1">("e1");
  const reduce = useReducedMotion();

  useEffect(() => {
    fetch("/api/metricas")
      .then((r) => r.json())
      .then(setPayload)
      .catch(() => {});
  }, []);

  const m = payload[sel];

  return (
    <main className="mx-auto max-w-7xl px-5 pb-16 pt-8">
      <motion.div
        initial={reduce ? { opacity: 0 } : { opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55, ease: [0.5, 0, 0.1, 1] }}
        className="mb-6"
      >
        <p className="eyebrow mb-2">Analítica de experimentos</p>
        <h1 className="text-3xl leading-none font-semibold tracking-tight text-ink md:text-4xl">
          Evidencia de resiliencia
        </h1>
      </motion.div>

      <div className="mb-6 flex items-center gap-2">
        {(["e0", "e1"] as const).map((k) => (
          <button
            key={k}
            onClick={() => setSel(k)}
            className={
              "px-4 py-2 text-[0.78rem] font-medium tracking-[0.2em] uppercase transition-colors border " +
              (sel === k
                ? "border-line bg-raised text-ink"
                : "border-transparent text-mut hover:text-ink")
            }
          >
            EXPERIMENTO {k.toUpperCase()}
          </button>
        ))}
      </div>

      <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4">
        <KpiCell etiqueta="Solicitudes" valor={m.total_requests.toLocaleString("es-AR")} delta="total emitidas" />
        <KpiCell etiqueta="Tasa de éxito" valor={`${m.success_rate.toFixed(1)}%`} delta={`${m.failed_requests} fallidas`} acento={m.success_rate >= 99} />
        <KpiCell etiqueta="Latencia media" valor={(m.latency_mean_ms ?? 0).toFixed(0)} unidad="ms" />
        <KpiCell
          etiqueta="Distribución"
          valor={Object.entries(m.distribucion_por_replica)
            .map(([k, v]) => `${k}:${v}`)
            .join(" · ")}
          delta="atendidas por réplica"
        />
      </div>

      <div className="mb-6">
        <MeasuredChart m={m} />
      </div>

      {sel === "e1" && m.deteccion ? (
        <div className="mb-6 grid gap-3 md:grid-cols-3">
          <div className="stamp card border-accent/40 px-4 py-3">
            <div className="mono-label text-faint">Inyección</div>
            <div className="num text-xl text-accent">R{m.inyeccion?.replica ?? "—"} · t+{hitoSeg(m, m.inyeccion?.ts)}s</div>
          </div>
          <div className="stamp card border-danger/40 px-4 py-3">
            <div className="mono-label text-danger">Detección</div>
            <div className="num text-xl text-danger">+{m.deteccion.tiempo_s.toFixed(2)}s</div>
            <div className="mono-label text-faint">desde inyección</div>
          </div>
          <div className="stamp card border-ok/40 px-4 py-3">
            <div className="mono-label text-ok">Recuperación</div>
            <div className="num text-xl text-ok">+{m.recuperacion?.tiempo_s?.toFixed(2) ?? "—"}s</div>
            <div className="mono-label text-faint">desde detección</div>
          </div>
        </div>
      ) : null}

      <QaPanel items={[...PREGUNTAS]} fuente={payload.fuente} />
    </main>
  );
}

function hitoSeg(m: Metricas, ts: number | undefined): number {
  if (ts === undefined) return 0;
  const dur = Math.max(m.serie_por_segundo.length, 1);
  const t0 = m.fecha - dur;
  return Math.max(0, Math.round(ts - t0));
}
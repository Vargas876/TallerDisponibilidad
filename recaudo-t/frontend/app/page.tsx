"use client";

import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { useDispatcher } from "@/lib/useDispatcher";
import { METRICAS_E1 } from "@/lib/defaultMetrics";
import { fmtAgo, fmtInt, fmtUptime } from "@/lib/format";
import { KpiCell } from "@/components/KpiCell";
import { ReplicaCard } from "@/components/ReplicaCard";
import { DetectionStamp } from "@/components/DetectionStamp";
import { TrafficArea } from "@/components/TrafficArea";
import { Timeline } from "@/components/Timeline";

export default function LivePage() {
  const { snapshot, conectado, serie, alarma, ultimoEvento, recientes } = useDispatcher();
  const [ahora, setAhora] = useState<number>(() => Date.now() / 1000);
  const reduce = useReducedMotion();

  useEffect(() => {
    const id = setInterval(() => setAhora(Date.now() / 1000), 1000);
    return () => clearInterval(id);
  }, []);

  const repOrdenadas = [...(snapshot?.replicas ?? [])].sort((a, b) =>
    a.id.localeCompare(b.id),
  );

  const sinTraficoCliente =
    conectado && (snapshot?.total_solicitudes ?? 0) === 0;
  const serieVis = sinTraficoCliente ? METRICAS_E1.serie_por_segundo : serie;

  return (
    <main className="mx-auto max-w-7xl px-5 pb-16 pt-8">
      <motion.div
        initial={reduce ? { opacity: 0 } : { opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55, ease: [0.5, 0, 0.1, 1] }}
        className="mb-8 flex flex-wrap items-end justify-between gap-4"
      >
        <div>
          <p className="eyebrow mb-2">Estado actual del sistema</p>
          <h1 className="text-3xl leading-none font-semibold tracking-tight text-ink md:text-4xl">
            {snapshot === null ? (
              "Conectando al dispatcher…"
            ) : (
              <span className={alarma ? "text-danger" : "text-ink"}>
                Disponibilidad bajo observación
              </span>
            )}
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <span className={"dot " + (conectado ? "dot-ok" : "dot-warn")} />
          <span className="mono-label text-mut">
            {conectado ? "canal en vivo" : "canal caído — reintentando"}
          </span>
        </div>
      </motion.div>

      <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4">
        <KpiCell etiqueta="Réplicas" valor={`${snapshot?.replicas_viva ?? 0}/${snapshot?.replicas.length ?? 0}`} unidad="vivas" acento={!alarma} />
        <KpiCell etiqueta="Solicitudes" valor={fmtInt(snapshot?.total_solicitudes ?? 0)} delta="total atendidas" />
        <KpiCell etiqueta="Uptime" valor={fmtUptime(snapshot?.uptime_s ?? 0)} delta="sesión del dispatcher" />
        <KpiCell etiqueta="Última detección" valor={snapshot?.last_detection ? `R${snapshot.last_detection.replica}` : "—"} delta={`hace ${fmtAgo(snapshot?.last_detection?.at ?? null, ahora)}`} />
      </div>

      <div className="mb-6 grid gap-3 md:grid-cols-3">
        {repOrdenadas.map((r) => (
          <ReplicaCard key={r.id} rep={r} ahora={ahora} />
        ))}
      </div>

      <div className="mb-6">
        <TrafficArea serie={serieVis} demo={sinTraficoCliente} />
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        <DetectionStamp replica={ultimoEvento?.replica ?? snapshot?.last_detection?.replica ?? null} ts={ultimoEvento?.ts ?? snapshot?.last_detection?.at ?? null} />
        <Timeline recientes={recientes} ahora={ahora} />
      </div>
    </main>
  );
}
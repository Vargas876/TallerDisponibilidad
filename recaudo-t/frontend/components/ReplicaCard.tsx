"use client";

import { motion } from "framer-motion";
import type { ReplicaState } from "@/lib/types";
import { fmtAgo, fmtInt, fmtLatency } from "@/lib/format";

export function ReplicaCard({ rep, ahora }: { rep: ReplicaState; ahora: number }) {
  const caida = rep.status === "CAIDA";
  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.985 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.35, ease: [0.5, 0, 0.1, 1] }}
      className={
        "card card-hover px-4 py-4 " + (caida ? "border-danger/40" : "")
      }
    >
      <div className="mb-3 flex items-start justify-between">
        <div className="flex items-baseline gap-3">
          <span className="num text-3xl font-semibold tracking-tight text-ink">
            {rep.id}
          </span>
          <span className="mono-label text-faint">réplica</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={"dot " + (caida ? "dot-down" : "dot-ok")} />
          <span
            className={
              "mono-label " + (caida ? "text-danger" : "text-ok")
            }
          >
            {rep.status}
          </span>
        </div>
      </div>

      <dl className="grid grid-cols-3 gap-x-3 gap-y-2 text-[0.72rem]">
        <dl className="contents">
          <dt className="mono-label text-faint">Ping</dt>
          <dd className="col-span-2 num text-mut">
            {fmtLatency(rep.latency_ms)}
            <span className="text-faint"> · {fmtAgo(rep.last_ping, ahora)}</span>
          </dd>
          <dt className="mono-label text-faint">Atendidos</dt>
          <dd className="col-span-2 num text-mut">{fmtInt(rep.total_requests)}</dd>
          <dt className="mono-label text-faint">Errores</dt>
          <dd className="col-span-2 num text-mut">{fmtInt(rep.failed_requests)}</dd>
          <dt className="mono-label text-faint">Caída previa</dt>
          <dd className="col-span-2 num text-mut">{fmtAgo(rep.last_down, ahora)}</dd>
        </dl>
      </dl>

      {caida ? (
        <div className="mt-3 border-t border-danger/25 pt-2">
          <span className="mono-label text-danger">
            {rep.consecutive_failures} fallos consecutivos
          </span>
        </div>
      ) : null}
    </motion.div>
  );
}
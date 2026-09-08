"use client";

import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { fmtClock } from "@/lib/format";

export function DetectionStamp({
  replica,
  ts,
}: {
  replica: string | null;
  ts: number | null;
}) {
  const reduce = useReducedMotion();
  return (
    <AnimatePresence mode="wait">
      {replica && ts ? (
        <motion.div
          key={`${replica}-${ts}`}
          initial={reduce ? { opacity: 0 } : { opacity: 0, scale: 0.94 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.45, ease: [0.5, 0, 0.1, 1] }}
          className="stamp card flex items-baseline justify-between gap-4 border-accent/40 px-4 py-3"
        >
          <div>
            <span className="mono-label text-faint">Detección de caída</span>
            <div className="mt-1 text-lg font-semibold tracking-[0.12em] text-ink uppercase">
              Réplica {replica} — no responde
            </div>
          </div>
          <div className="text-right">
            <div className="mono-label text-accent">registrado</div>
            <div className="num text-mut">{ts ? fmtClock(ts) : "—"}</div>
          </div>
        </motion.div>
      ) : (
        <motion.div
          key="idle"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="card flex items-center justify-between px-4 py-3"
        >
          <div>
            <span className="mono-label text-faint">Detección de caída</span>
            <div className="mt-1 text-base text-mut">
              Sin incidencias registradas durante esta sesión
            </div>
          </div>
          <span className="dot dot-ok" />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
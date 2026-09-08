"use client";

import { motion } from "framer-motion";

export function KpiCell({
  etiqueta,
  valor,
  delta,
  unidad = "",
  acento = false,
}: {
  etiqueta: string;
  valor: string;
  delta?: string;
  unidad?: string;
  acento?: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.5, 0, 0.1, 1] }}
      className="card px-4 py-3"
    >
      <div className="mono-label text-faint mb-1.5">{etiqueta}</div>
      <div
        className={
          "num text-2xl leading-none tracking-tight " +
          (acento ? "text-accent" : "text-ink")
        }
      >
        {valor}
        {unidad ? <span className="ml-0.5 text-base text-mut">{unidad}</span> : null}
      </div>
      {delta ? <div className="mt-1 text-[0.7rem] text-mut tabular">{delta}</div> : null}
    </motion.div>
  );
}
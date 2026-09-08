"use client";

import { motion } from "framer-motion";
import { fmtClock } from "@/lib/format";

export interface Evento {
  ts: number;
  texto: string;
  tipo: string;
}

export function Timeline({ recientes, ahora }: { recientes: Evento[]; ahora: number }) {
  if (recientes.length === 0) {
    return (
      <div className="card flex items-center justify-center px-4 py-8">
        <span className="mono-label text-faint">
          Sin transiciones de estado · las réplicas responden normal
        </span>
      </div>
    );
  }
  return (
    <div className="card px-4 py-3">
      <div className="mono-label text-faint mb-3">Bitácora de transiciones</div>
      <ul className="space-y-1.5">
        {recientes.map((e, i) => {
          const caida = e.tipo === "down";
          return (
            <motion.li
              key={`${e.ts}-${i}`}
              initial={{ opacity: 0, x: 6 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, ease: [0.5, 0, 0.1, 1] }}
              className="flex items-baseline gap-3 border-l-2 pl-3 text-[0.78rem] leading-relaxed"
              style={{
                borderColor: caida
                  ? "var(--c-danger)"
                  : "var(--c-ok)",
              }}
            >
              <span className="num text-faint shrink-0">{fmtClock(e.ts)}</span>
              <span className={caida ? "text-danger" : "text-ok"}>{e.texto}</span>
            </motion.li>
          );
        })}
      </ul>
      <div className="mt-3 border-t border-linedim pt-2">
        <span className="mono-label text-faint">última transición hace </span>{" "}
        <span className="num text-mut">
          {Math.max(0, ahora - recientes[0].ts).toFixed(1)}s
        </span>
      </div>
    </div>
  );
}
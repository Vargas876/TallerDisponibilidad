"use client";

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import type { PuntoSerie } from "@/lib/types";

export function TrafficArea({
  serie,
  demo = false,
}: {
  serie: PuntoSerie[];
  demo?: boolean;
}) {
  return (
    <div className="card px-4 py-4">
      <div className="mb-3 flex items-center justify-between">
        <span className="mono-label text-faint">
          Carga — {demo ? "muestra del experimento E1 (medición)" : "enmascaramiento en vivo"}
        </span>
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-2 text-[0.7rem] text-mut tabular">
            <span className="dot dot-ok" /> ok
          </span>
          <span className="flex items-center gap-2 text-[0.7rem] text-mut tabular">
            <span className="dot dot-down" /> fallos
          </span>
        </div>
      </div>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={serie} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
            <defs>
              <linearGradient id="gOk" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--c-ok)" stopOpacity={0.28} />
                <stop offset="100%" stopColor="var(--c-ok)" stopOpacity={0.02} />
              </linearGradient>
              <linearGradient id="gFail" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--c-danger)" stopOpacity={0.4} />
                <stop offset="100%" stopColor="var(--c-danger)" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid
              stroke="var(--c-linedim)"
              strokeDasharray="2 4"
              vertical={false}
            />
            <XAxis
              dataKey="seg"
              tickFormatter={(s: number) => `${s}`}
              stroke="var(--c-faint)"
              fontSize={10}
              tickLine={false}
              axisLine={false}
              fontFamily="var(--font-jetbrains)"
            />
            <YAxis
              stroke="var(--c-faint)"
              fontSize={10}
              width={34}
              tickLine={false}
              axisLine={false}
              allowDecimals={false}
              fontFamily="var(--font-jetbrains)"
            />
            <Tooltip
              contentStyle={{
                background: "var(--c-raised)",
                border: "1px solid var(--c-line)",
                borderRadius: 0,
                fontSize: 12,
                fontFamily: "var(--font-jetbrains)",
                color: "var(--c-ink)",
              }}
              labelFormatter={(s) => `seg ${String(s)}`}
            />
            <Area
              type="monotone"
              name="ok"
              dataKey="ok"
              stroke="var(--c-ok)"
              strokeWidth={1.5}
              fill="url(#gOk)"
              isAnimationActive={false}
            />
            <Area
              type="monotone"
              name="fallos"
              dataKey="fail"
              stroke="var(--c-danger)"
              strokeWidth={1.5}
              fill="url(#gFail)"
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      {demo && (
        <p className="mt-3 border-t border-line pt-3 text-[0.68rem] leading-relaxed text-mut tabular">
          Sin tráfico de cliente en vivo: al abrir el panel no hay ningún
          `client.py` generando solicitudes contra el dispatcher. La gráfica
          muestra la medición real del experimento E1 (20 req/s). Para ver carga
          en vivo ejecuta:
          <code className="ml-1 font-mono text-ink">
            python backend/client/client.py --url https://recaudo-t-dispatcher.onrender.com
          </code>
        </p>
      )}
    </div>
  );
}
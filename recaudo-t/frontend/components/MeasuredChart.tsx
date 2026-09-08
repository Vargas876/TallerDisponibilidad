"use client";

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from "recharts";
import type { Metricas } from "@/lib/types";

function hitoSeg(m: Metricas, ts: number | undefined): number {
  if (ts === undefined) return -1;
  const dur = Math.max(m.serie_por_segundo.length, 1);
  const t0 = m.fecha - dur;
  return Math.max(0, Math.round(ts - t0));
}

export function MeasuredChart({ m }: { m: Metricas }) {
  const segIny = hitoSeg(m, m.inyeccion?.ts);
  const segDet = hitoSeg(m, m.deteccion?.ts);
  const segRec = hitoSeg(m, m.recuperacion?.ts);

  return (
    <div className="card px-4 py-4">
      <div className="mb-3 flex items-center justify-between">
        <span className="mono-label text-faint">
          Serie por segundo — solicitudes del cliente
        </span>
        {m.deteccion ? (
          <span className="num text-xs text-mut">
            detección en el segundo {segDet}
          </span>
        ) : null}
      </div>
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={m.serie_por_segundo} margin={{ top: 8, right: 8, bottom: 0, left: 4 }}>
            <defs>
              <linearGradient id="gOk2" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--c-ok)" stopOpacity={0.3} />
                <stop offset="100%" stopColor="var(--c-ok)" stopOpacity={0.02} />
              </linearGradient>
              <linearGradient id="gFail2" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--c-danger)" stopOpacity={0.35} />
                <stop offset="100%" stopColor="var(--c-danger)" stopOpacity={0.04} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="var(--c-linedim)" strokeDasharray="2 4" vertical={false} />
            <XAxis
              dataKey="seg"
              tickFormatter={(s: number) => `${s}s`}
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
            {segIny >= 0 ? (
              <ReferenceLine x={segIny} stroke="var(--c-accent)" strokeWidth={1.5} strokeDasharray="4 3" label={{ value: "inyección", fontSize: 10, fill: "var(--c-accent)", fontFamily: "var(--font-jetbrains)", position: "insideTopLeft" }} />
            ) : null}
            {segDet >= 0 ? (
              <ReferenceLine x={segDet} stroke="var(--c-danger)" strokeWidth={1.5} label={{ value: "detección", fontSize: 10, fill: "var(--c-danger)", fontFamily: "var(--font-jetbrains)", position: "insideTopLeft" }} />
            ) : null}
            {segRec >= 0 ? (
              <ReferenceLine x={segRec} stroke="var(--c-ok)" strokeWidth={1.5} strokeDasharray="4 3" label={{ value: "recuperación", fontSize: 10, fill: "var(--c-ok)", fontFamily: "var(--font-jetbrains)", position: "insideTopLeft" }} />
            ) : null}
            <Area
              type="monotone"
              name="exitosas"
              dataKey="ok"
              stroke="var(--c-ok)"
              strokeWidth={1.5}
              fill="url(#gOk2)"
              isAnimationActive={false}
              dot={false}
            />
            <Area
              type="monotone"
              name="fallidas"
              dataKey="fail"
              stroke="var(--c-danger)"
              strokeWidth={1.5}
              fill="url(#gFail2)"
              isAnimationActive={false}
              dot={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
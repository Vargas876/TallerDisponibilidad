import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import type { PuntoSerie } from "@/lib/types"

export function RequestsChart({ serie }: { serie: PuntoSerie[] }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={serie} margin={{ top: 8, right: 8, left: -16, bottom: 0 }} barCategoryGap="15%">
        <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.3 0.02 250 / 0.4)" vertical={false} />
        <XAxis
          dataKey="seg"
          tick={{ fill: "oklch(0.66 0.02 250)", fontSize: 11 }}
          axisLine={{ stroke: "oklch(0.3 0.02 250 / 0.4)" }}
          tickLine={false}
          label={{ value: "segundo", position: "insideBottomRight", offset: -4, fill: "oklch(0.66 0.02 250)", fontSize: 10 }}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fill: "oklch(0.66 0.02 250)", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          cursor={{ fill: "oklch(0.3 0.02 250 / 0.15)" }}
          contentStyle={{
            background: "oklch(0.2 0.015 250)",
            border: "1px solid oklch(0.3 0.02 250)",
            borderRadius: 8,
            fontSize: 12,
            color: "oklch(0.97 0.004 250)",
          }}
          labelFormatter={(v) => `Segundo ${v}`}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="ok" name="Éxitos" stackId="a" fill="var(--success)" radius={[3, 3, 0, 0]} />
        <Bar dataKey="fail" name="Fallos" stackId="a" fill="var(--danger)" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
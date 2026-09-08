import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts"

const COLORS = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)", "var(--chart-5)"]

export function ReplicasPie({ replicas }: { replicas: Record<string, number> }) {
  const data = Object.entries(replicas).map(([name, value]) => ({ name, value }))

  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={92}
          paddingAngle={3}
          dataKey="value"
          stroke="transparent"
        >
          {data.map((entry, i) => (
            <Cell key={entry.name} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            background: "oklch(0.2 0.015 250)",
            border: "1px solid oklch(0.3 0.02 250)",
            borderRadius: 8,
            fontSize: 12,
            color: "oklch(0.97 0.004 250)",
          }}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}
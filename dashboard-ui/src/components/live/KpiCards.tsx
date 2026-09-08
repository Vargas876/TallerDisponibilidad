import { Activity, Server, Timer, UserCheck } from "lucide-react"
import { cn } from "@/lib/utils"
import { ReplicaPill } from "@/lib/hooks"
import type { EstadoInfo } from "@/lib/types"

type Tone = "primary" | "success" | "warning" | "danger" | "default"

const toneMap: Record<Tone, { card: string; value: string; icon: string }> = {
  primary: {
    card: "bg-blue-500/10 ring-1 ring-blue-500/20 dark:bg-blue-900/25 dark:ring-blue-800/40",
    value: "text-blue-600 dark:text-blue-300",
    icon: "text-blue-500 dark:text-blue-400",
  },
  success: {
    card: "bg-emerald-500/10 ring-1 ring-emerald-500/20 dark:bg-emerald-900/25 dark:ring-emerald-800/40",
    value: "text-emerald-600 dark:text-emerald-300",
    icon: "text-emerald-500 dark:text-emerald-400",
  },
  warning: {
    card: "bg-amber-500/10 ring-1 ring-amber-500/20 dark:bg-amber-900/25 dark:ring-amber-800/40",
    value: "text-amber-600 dark:text-amber-300",
    icon: "text-amber-500 dark:text-amber-400",
  },
  danger: {
    card: "bg-rose-500/10 ring-1 ring-rose-500/20 dark:bg-rose-900/25 dark:ring-rose-800/40",
    value: "text-rose-600 dark:text-rose-300",
    icon: "text-rose-500 dark:text-rose-400",
  },
  default: {
    card: "bg-card ring-1 ring-border",
    value: "text-foreground",
    icon: "text-muted-foreground",
  },
}

export function KpiCards({ estado }: { estado: EstadoInfo | null }) {
  const total = estado?.total_solicitudes ?? 0
  const states = estado?.estado ?? {}
  const ids = Object.keys(states)
  const vivas = ids.filter((k) => states[k] === "VIVA").length

  const kpis: {
    label: string
    value: string
    caption: string
    icon: React.ReactNode
    tone: Tone
  }[] = [
    {
      label: "Solicitudes atendidas",
      value: total.toLocaleString("es-AR"),
      caption: "vía dispatcher",
      icon: <Activity className="size-5" />,
      tone: "primary",
    },
    {
      label: "Réplicas VIVA",
      value: `${vivas} / ${ids.length || "–"}`,
      caption: "en línea",
      icon: <Server className="size-5" />,
      tone: "success",
    },
    {
      label: "Objetivo detección",
      value: "≤ 3 s",
      caption: "≈ T × k",
      icon: <Timer className="size-5" />,
      tone: "warning",
    },
    {
      label: "Disponibilidad",
      value: total > 0 ? "En vivo" : "—",
      caption: "sin errores de cliente",
      icon: <UserCheck className="size-5" />,
      tone: "default",
    },
  ]

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {kpis.map((kpi) => {
        const t = toneMap[kpi.tone]
        return (
          <div
            key={kpi.label}
            className={cn("relative overflow-hidden rounded-xl p-4", t.card)}
          >
            <span className="pointer-events-none absolute -right-6 -top-6 inline-flex size-16 rounded-full bg-black/5 dark:bg-white/5" />
            <span className="pointer-events-none absolute -right-2 -top-2 inline-flex size-8 rounded-full bg-black/5 dark:bg-white/5" />
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-1">
                <p className="text-sm font-medium text-muted-foreground">{kpi.label}</p>
                <p className={cn("text-2xl font-bold tracking-tight", t.value)}>{kpi.value}</p>
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  {kpi.label === "Réplicas VIVA" && <ReplicaPill estado={vivas > 0 ? "VIVA" : undefined} />}
                  {kpi.label === "Réplicas VIVA" ? null : kpi.caption}
                </div>
              </div>
              <span className={cn("shrink-0", t.icon)}>{kpi.icon}</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
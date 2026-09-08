import { Server, Wifi, WifiOff } from "lucide-react"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import type { ReplicaState } from "@/lib/types"

const PALETTE: Record<string, string> = {
  A: "from-sky-500/20 to-sky-500/5 border-sky-500/40 text-sky-300",
  B: "from-violet-500/20 to-violet-500/5 border-violet-500/40 text-violet-300",
  C: "from-emerald-500/20 to-emerald-500/5 border-emerald-500/40 text-emerald-300",
  D: "from-amber-500/20 to-amber-500/5 border-amber-500/40 text-amber-300",
}

export function ReplicaCard({ id, estado }: { id: string; estado?: ReplicaState }) {
  const up = estado === "VIVA"
  const palette = PALETTE[id] ?? "from-slate-500/20 to-slate-500/5 border-slate-500/40 text-slate-300"

  return (
    <Card
      className={cn(
        "group relative overflow-hidden bg-gradient-to-br p-4 transition-all",
        palette,
        up
          ? "shadow-[0_0_24px_-8px_rgba(52,211,153,0.45)]"
          : "shadow-[0_0_18px_-6px_rgba(248,113,113,0.5)]"
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex size-10 items-center justify-center rounded-lg bg-foreground/5 text-xl font-bold">
          {id}
        </div>
        <div
          className={cn(
            "flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold",
            up
              ? "bg-emerald-500/15 text-emerald-300 ring-1 ring-inset ring-emerald-500/30"
              : "bg-red-500/15 text-red-300 ring-1 ring-inset ring-red-500/30"
          )}
        >
          {up ? <Wifi className="size-3.5" /> : <WifiOff className="size-3.5" />}
          {up ? "VIVA" : "CAÍDA"}
        </div>
      </div>
      <p className="mt-4 flex items-center gap-1.5 text-[11px] font-medium text-foreground/50">
        <Server className="size-3.5" />
        Réplica {id}
      </p>
      <div className="mt-1 flex items-center gap-1.5">
        <span className={cn("inline-block size-2 rounded-full", up ? "bg-emerald-400 pulse-dot" : "bg-red-400")} />
        <span className="text-xs text-muted-foreground">{up ? "Respondiendo" : "Fuera de línea"}</span>
      </div>
    </Card>
  )
}
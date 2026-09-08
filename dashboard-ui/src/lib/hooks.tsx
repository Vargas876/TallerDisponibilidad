import { useEffect, useState } from "react"
import { cn } from "@/lib/utils"

export function useNow(intervalMs: number): number {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), intervalMs)
    return () => window.clearInterval(id)
  }, [intervalMs])
  return now
}

export function usePolling<T>(fn: () => Promise<T>, intervalMs: number, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    const run = async () => {
      try {
        const result = await fn()
        if (active) {
          setData(result)
          setError(null)
        }
      } catch (e) {
        if (active) setError(e instanceof Error ? e.message : "Error")
      }
    }
    void run()
    const id = window.setInterval(run, intervalMs)
    return () => {
      active = false
      window.clearInterval(id)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intervalMs, ...deps])

  return { data, error }
}

export function ReplicaPill({ estado, className }: { estado?: string; className?: string }) {
  const up = estado === "VIVA"
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold",
        up
          ? "bg-emerald-500/10 text-emerald-400 ring-1 ring-inset ring-emerald-500/30"
          : "bg-red-500/10 text-red-400 ring-1 ring-inset ring-red-500/30",
        className
      )}
    >
      <span className={cn("size-1.5 rounded-full", up ? "bg-emerald-400 pulse-dot" : "bg-red-400")} />
      {up ? "VIVA" : "CAÍDA"}
    </span>
  )
}
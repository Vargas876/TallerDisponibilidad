import { Search, ScrollText } from "lucide-react"
import { useEffect, useMemo, useRef, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

export interface ParsedLog {
  ts: number | null
  texto: string
  tipo: "caida" | "viva" | "info"
}

export function parseLines(lineas: string[]): ParsedLog[] {
  return lineas.map((l) => {
    const m = /^\[(\d+\.\d+)\]\s*(.*)$/.exec(l)
    if (!m) return { ts: null, texto: l, tipo: "info" }
    const texto = m[2]
    let tipo: ParsedLog["tipo"] = "info"
    if (/VIVA -> CA(?:I|Í)DA/.test(texto)) tipo = "caida"
    else if (/CA(?:I|Í)DA -> VIVA|recuperada/.test(texto)) tipo = "viva"
    return { ts: parseFloat(m[1]), texto, tipo }
  })
}

export function formatHora(ts: number): string {
  const d = new Date(ts * 1000)
  const hh = String(d.getHours()).padStart(2, "0")
  const mm = String(d.getMinutes()).padStart(2, "0")
  const ss = String(d.getSeconds()).padStart(2, "0")
  const ml = String(d.getMilliseconds()).padStart(3, "0")
  return `${hh}:${mm}:${ss}.${ml}`
}

const levelBadge: Record<ParsedLog["tipo"], { label: string; cls: string }> = {
  caida: {
    label: "CAÍDA",
    cls: "bg-red-500/10 text-red-500 dark:text-red-400 ring-red-500/20",
  },
  viva: {
    label: "RECUP",
    cls: "bg-emerald-500/10 text-emerald-500 dark:text-emerald-400 ring-emerald-500/20",
  },
  info: {
    label: "INFO",
    cls: "bg-sky-500/10 text-sky-500 dark:text-sky-400 ring-sky-500/20",
  },
}

type Filtro = "todos" | "caida" | "viva" | "info"

const FILTROS: { id: Filtro; label: string }[] = [
  { id: "todos", label: "Todos" },
  { id: "caida", label: "Caídas" },
  { id: "viva", label: "Recuperaciones" },
  { id: "info", label: "Info" },
]

export function LogPanel({ lineas }: { lineas: string[] }) {
  const logs = useMemo(() => parseLines(lineas), [lineas])
  const [busqueda, setBusqueda] = useState("")
  const [filtro, setFiltro] = useState<Filtro>("todos")
  const ref = useRef<HTMLDivElement>(null)

  const visibles = useMemo(() => {
    const q = busqueda.trim().toLowerCase()
    return logs.filter((l) => {
      if (filtro !== "todos" && l.tipo !== filtro) return false
      if (q && !l.texto.toLowerCase().includes(q)) return false
      return true
    })
  }, [logs, busqueda, filtro])

  useEffect(() => {
    const el = ref.current
    if (el) el.scrollTop = el.scrollHeight
  }, [visibles.length])

  return (
    <Card className="flex h-full min-h-[420px] flex-col">
      <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3 space-y-0 pb-3">
        <CardTitle className="flex items-center gap-2 text-sm font-semibold">
          <ScrollText className="size-4 text-muted-foreground" />
          Bitácora del monitor
        </CardTitle>
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              placeholder="Buscar…"
              className="h-8 w-40 pl-8 text-xs"
            />
          </div>
          <div className="flex items-center gap-1 rounded-lg bg-muted p-0.5">
            {FILTROS.map((f) => (
              <button
                key={f.id}
                onClick={() => setFiltro(f.id)}
                className={cn(
                  "rounded-md px-2.5 py-1 text-[11px] font-medium transition-colors",
                  filtro === f.id
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div
          ref={ref}
          className="log-scroll h-[280px] overflow-y-auto rounded-md border border-border bg-background/70"
        >
          {visibles.length === 0 && (
            <p className="p-4 text-xs text-muted-foreground/70">
              Sin eventos para el filtro actual. Iniciá la red para ver actividad…
            </p>
          )}
          {visibles.map((log, i) => {
            const b = levelBadge[log.tipo]
            return (
              <div
                key={`${log.ts}-${i}`}
                className="flex items-center gap-3 border-b border-border/40 px-3 py-2 last:border-b-0 hover:bg-muted/40"
              >
                {log.ts === null ? (
                  <span className="w-[68px] shrink-0" />
                ) : (
                  <time className="w-[68px] shrink-0 font-mono text-[11px] text-muted-foreground">
                    {formatHora(log.ts)}
                  </time>
                )}
                <Badge variant="outline" className={cn("shrink-0 capitalize", b.cls)}>
                  {b.label}
                </Badge>
                <span
                  className={cn(
                    "truncate font-mono text-[11px]",
                    log.tipo === "caida"
                      ? "text-red-400"
                      : log.tipo === "viva"
                        ? "text-emerald-400"
                        : "text-foreground/80"
                  )}
                >
                  {log.texto}
                </span>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
import { useCallback, useEffect, useMemo, useState } from "react"
import { Ban, CheckCircle2, FileSpreadsheet, Loader2, RefreshCw, TrendingUp, XCircle } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { getInyector, getResultado, getResultados } from "@/lib/api"
import type { InyectorInfo, ResultadoProcesado } from "@/lib/types"
import { formatTs } from "@/lib/utils"
import { RequestsChart } from "@/components/charts/RequestsChart"
import { ReplicasPie } from "@/components/charts/ReplicasPie"

export function ResultsView() {
  const [archivos, setArchivos] = useState<string[]>([])
  const [seleccion, setSeleccion] = useState<string>("")
  const [resultado, setResultado] = useState<ResultadoProcesado | null>(null)
  const [inyector, setInyector] = useState<InyectorInfo | null>(null)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const cargar = useCallback(async (archivo: string) => {
    if (!archivo) return
    setCargando(true)
    setError(null)
    try {
      const [res, inj] = await Promise.all([getResultado(archivo), getInyector()])
      setResultado(res)
      setInyector(inj)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar")
    } finally {
      setCargando(false)
    }
  }, [])

  useEffect(() => {
    getResultados()
      .then((d) => {
        setArchivos(d.archivos)
        if (d.archivos.length > 0) {
          setSeleccion(d.archivos[0])
          return cargar(d.archivos[0])
        }
      })
      .catch(() => setError("No hay resultados disponibles"))
  }, [cargar])

  const deteccion = useMemo(() => {
    if (resultado && inyector?.timestamp) {
      return { inyectorTs: inyector.timestamp, replica: inyector.replica }
    }
    return null
  }, [resultado, inyector])

  const metricas = [
    { label: "Total solicitudes", value: resultado?.total, icon: <FileSpreadsheet className="size-4" /> },
    { label: "Exitosas", value: resultado?.exitosos, icon: <CheckCircle2 className="size-4" />, tone: "text-emerald-400" },
    { label: "Fallidas", value: resultado?.fallidos, icon: <XCircle className="size-4" />, tone: "text-red-400" },
    { label: "% éxito", value: resultado ? `${resultado.porcentaje}%` : undefined, icon: <TrendingUp className="size-4" />, tone: "text-sky-400" },
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Resultados</h1>
          <p className="text-sm text-muted-foreground">
            Métricas de las corridas E0 / E1 a partir de los CSVs generados por el cliente.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={seleccion} onValueChange={(v) => { setSeleccion(v); void cargar(v) }}>
            <SelectTrigger className="w-[220px]">
              <SelectValue placeholder="Seleccionar CSV" />
            </SelectTrigger>
            <SelectContent>
              {archivos.map((a) => (
                <SelectItem key={a} value={a}>{a}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" size="icon" onClick={() => seleccion && void cargar(seleccion)}>
            <RefreshCw className="size-4" />
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTitle>Problema al leer resultados</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metricas.map((m) => (
          <Card key={m.label}>
            <CardContent className="flex items-center gap-4 p-4">
              <div className={`flex size-10 items-center justify-center rounded-lg bg-muted ${m.tone ?? "text-muted-foreground"}`}>
                {m.icon}
              </div>
              <div className="min-w-0">
                <p className="text-xs font-medium text-muted-foreground">{m.label}</p>
                {cargando ? (
                  <Skeleton className="mt-1 h-6 w-16" />
                ) : (
                  <p className="truncate text-xl font-bold tracking-tight">{m.value ?? "–"}</p>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-5">
        <Card className="xl:col-span-3">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">
              Solicitudes por segundo — {resultado?.archivo ?? "sin archivo"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {cargando ? (
              <Skeleton className="h-[280px] w-full" />
            ) : (
              <RequestsChart serie={resultado?.serie ?? []} />
            )}
          </CardContent>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold">Distribución por réplica</CardTitle>
          </CardHeader>
          <CardContent>
            {cargando ? (
              <Skeleton className="h-[280px] w-full" />
            ) : (
              <ReplicasPie replicas={resultado?.replicas ?? {}} />
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold">Cálculo del tiempo de detección</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <DetRow label="Timestamp de inyección" value={deteccion?.inyectorTs ? formatTs(deteccion.inyectorTs) : "—"} />
          <DetRow label="Timestamp VIVA → CAÍDA" value="Ver bitácora" hint="[ts] RÉPLICA VIVA → CAIDA" />
          <DetRow
            label="Diferencia"
            value="≈ T × k"
            hint="Esperado ~2 s con T=1, k=2"
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm font-semibold">
            <Ban className="size-4 text-muted-foreground" />
            Verificación del experimento
          </CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-3">
          <CheckRow estado={resultado ? resultado.total > 0 : false}>
            CSV con solicitudes registradas (timestamp_envio, exito, réplica)
          </CheckRow>
          <CheckRow estado={resultado ? resultado.replicas && Object.keys(resultado.replicas).length > 1 : false}>
            Más de una réplica respondió (redundancia activa compitiendo)
          </CheckRow>
          <CheckRow estado={resultado ? resultado.porcentaje >= 95 : false}>
            Éxito ≥ 95% durante la ventana de caída
          </CheckRow>
        </CardContent>
      </Card>
    </div>
  )
}

function DetRow({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-lg border border-border bg-muted/40 p-3">
      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 font-mono text-sm font-semibold">{value}</p>
      {hint && <p className="mt-1 text-[11px] text-muted-foreground/80">{hint}</p>}
    </div>
  )
}

function CheckRow({ estado, children }: { estado: boolean; children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-2.5">
      {estado ? (
        <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-400" />
      ) : (
        <Loader2 className="mt-0.5 size-4 shrink-0 animate-spin text-muted-foreground" />
      )}
      <span className="text-muted-foreground">{children}</span>
    </div>
  )
}
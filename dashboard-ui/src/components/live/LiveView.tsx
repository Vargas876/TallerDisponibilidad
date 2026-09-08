import { Box, GitPullRequestArrow, Loader2, Radio } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { useNow, usePolling, ReplicaPill } from "@/lib/hooks"
import { getEstado, getBitacora, getInyector } from "@/lib/api"
import { formatTs } from "@/lib/utils"
import { KpiCards } from "./KpiCards"
import { ReplicaCard } from "./ReplicaCard"
import { LogPanel } from "./LogPanel"

export function LiveView() {
  const { data: estado, error: estadoError } = usePolling(getEstado, 1000)
  const { data: bitacora } = usePolling(getBitacora, 1500)
  const { data: inyector } = usePolling(getInyector, 3000)
  const now = useNow(1000)

  const online = estado?.disponible === true
  const estadoInfo = estado?.estado

  return (
    <div className="space-y-6">
      {/* Cabecera */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">En vivo</h1>
          <p className="text-sm text-muted-foreground">
            Monitoreo en tiempo real del dispatcher y sus réplicas.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            variant="outline"
            className={
              online ? "border-emerald-500/40 text-emerald-400" : "border-red-500/40 text-red-400"
            }
          >
            <span className="mr-1.5 inline-block size-1.5 rounded-full bg-current pulse-dot" />
            {online ? "Dispatcher en línea" : "Dispatcher offline"}
          </Badge>
          <Badge variant="secondary" className="font-mono">
            {new Date(now).toLocaleTimeString("es-AR", { hour12: false })}
          </Badge>
        </div>
      </div>

      {estadoError && (
        <Alert variant="destructive">
          <AlertTitle>No se pudo conectar con el backend</AlertTitle>
          <AlertDescription>
            Verificá que dispatcher y dashboard estén corriendo (error: {estadoError}).
          </AlertDescription>
        </Alert>
      )}

      {/* KPIs */}
      <KpiCards estado={estadoInfo ?? null} />

      {/* Réplicas */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm font-semibold">
            <Radio className="size-4 text-muted-foreground" />
            Réplicas
          </CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {estadoInfo &&
            Object.entries(estadoInfo.estado ?? {}).map(([id, st]) => (
              <ReplicaCard key={id} id={id} estado={st} />
            ))}
          {!estadoInfo && (
            <div className="col-span-full flex h-24 items-center justify-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              Esperando datos del dispatcher…
            </div>
          )}
        </CardContent>
      </Card>

      {/* Bitácora + inyector */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <LogPanel lineas={bitacora?.lineas ?? []} />
        </div>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm font-semibold">
              <GitPullRequestArrow className="size-4 text-muted-foreground" />
              Inyección de fallas
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between rounded-lg border border-border bg-muted/40 p-3">
              <span className="flex items-center gap-2 text-xs text-muted-foreground">
                <Box className="size-3.5" />
                Última inyección
              </span>
              {inyector?.replica ? (
                <ReplicaPill estado={estadoInfo?.estado?.[inyector.replica]} />
              ) : (
                <span className="text-xs text-muted-foreground">—</span>
              )}
            </div>

            <Separator />

            <div>
              <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Réplica objetivo</p>
              <p className="mt-1 font-mono text-lg font-semibold">{inyector?.replica ?? "—"}</p>
            </div>
            <div>
              <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                Timestamp de la inyección
              </p>
              <p className="mt-1 font-mono text-sm">{inyector?.timestamp ? formatTs(inyector.timestamp) : "—"}</p>
            </div>

            <Separator />

            <p className="text-xs leading-relaxed text-muted-foreground">
              El inyector se ejecuta a mano para tumbar una réplica:{" "}
              <code className="rounded bg-muted px-1 py-0.5 font-mono text-[11px]">
                python inyector.py &lt;ID&gt;
              </code>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
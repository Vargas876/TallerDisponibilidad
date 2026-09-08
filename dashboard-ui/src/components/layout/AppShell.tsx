import { Activity, BarChart3, ShieldCheck, Waypoints } from "lucide-react"
import { cn } from "@/lib/utils"
import { Separator } from "@/components/ui/separator"

type ViewId = "live" | "results"

interface NavItem {
  id: ViewId
  label: string
  icon: React.ReactNode
}

const NAV: NavItem[] = [
  { id: "live", label: "En vivo", icon: <Activity className="size-4" /> },
  { id: "results", label: "Resultados", icon: <BarChart3 className="size-4" /> },
]

export function AppShell({
  view,
  onViewChange,
  children,
}: {
  view: ViewId
  onViewChange: (v: ViewId) => void
  children: React.ReactNode
}) {
  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col border-r border-border bg-card/60 backdrop-blur lg:flex">
        <div className="flex items-center gap-2.5 px-5 py-5">
          <div className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <ShieldCheck className="size-5" />
          </div>
          <div>
            <p className="text-sm font-semibold leading-tight">RECAUDO-T</p>
            <p className="text-[11px] text-muted-foreground">Disponibilidad</p>
          </div>
        </div>
        <Separator />
        <nav className="flex-1 space-y-1 px-3 py-4">
          {NAV.map((item) => (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              className={cn(
                "flex w-full items-center gap-2.5 rounded-md px-3 py-2.5 text-sm font-medium transition-colors",
                view === item.id
                  ? "bg-secondary text-foreground shadow-sm"
                  : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
              )}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </nav>
        <div className="px-5 pb-5">
          <div className="rounded-lg border border-border bg-muted/40 p-3">
            <p className="flex items-center gap-1.5 text-[11px] font-medium text-muted-foreground">
              <Waypoints className="size-3.5" />
              Ping/Echo + Redundancia
            </p>
            <p className="mt-1 text-[10px] leading-relaxed text-muted-foreground/80">
              Detección de fallas y recuperación transparente para el cliente.
            </p>
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex min-h-screen w-full flex-1 flex-col lg:pl-60">
        <MobileNav view={view} onViewChange={onViewChange} />
        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  )
}

function MobileNav({ view, onViewChange }: { view: ViewId; onViewChange: (v: ViewId) => void }) {
  return (
    <div className="sticky top-0 z-20 flex items-center gap-1 border-b border-border bg-background/90 px-4 py-3 backdrop-blur lg:hidden">
      <div className="flex size-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
        <ShieldCheck className="size-4" />
      </div>
      <span className="mr-3 text-sm font-semibold">RECAUDO-T</span>
      {NAV.map((item) => (
        <button
          key={item.id}
          onClick={() => onViewChange(item.id)}
          className={cn(
            "flex flex-1 items-center justify-center gap-1.5 rounded-md px-2 py-1.5 text-xs font-medium",
            view === item.id ? "bg-secondary text-foreground" : "text-muted-foreground"
          )}
        >
          {item.icon}
          {item.label}
        </button>
      ))}
    </div>
  )
}
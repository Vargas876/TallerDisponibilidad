import { useState } from "react"
import { AppShell } from "@/components/layout/AppShell"
import { LiveView } from "@/components/live/LiveView"
import { ResultsView } from "@/components/results/ResultsView"

type ViewId = "live" | "results"

export default function App() {
  const [view, setView] = useState<ViewId>("live")

  return (
    <AppShell view={view} onViewChange={setView}>
      {view === "live" ? <LiveView /> : <ResultsView />}
    </AppShell>
  )
}
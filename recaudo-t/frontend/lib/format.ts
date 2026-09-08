export function fmtInt(n: number | null | undefined): string {
  if (n === null || n === undefined) return "—";
  return n.toLocaleString("es-AR");
}

export function fmtLatency(ms: number | null | undefined): string {
  if (ms === null || ms === undefined) return "—";
  if (ms < 1) return "<1ms";
  return `${ms.toFixed(0)}ms`;
}

export function fmtAgo(epoch: number | null | undefined, now: number): string {
  if (epoch === null || epoch === undefined) return "—";
  const d = Math.max(0, now - epoch);
  if (d < 1) return "ahora";
  if (d < 60) return `hace ${d.toFixed(0)}s`;
  const m = Math.floor(d / 60);
  return `hace ${m}m ${Math.floor(d % 60)}s`;
}

export function fmtClock(epoch: number | null | undefined): string {
  if (epoch === null || epoch === undefined) return "—";
  return new Date(epoch * 1000).toLocaleTimeString("es-AR", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function fmtUptime(s: number | null | undefined): string {
  if (s === null || s === undefined) return "—";
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = Math.floor(s % 60);
  if (h > 0) return `${h}h ${m}m ${sec}s`;
  if (m > 0) return `${m}m ${sec}s`;
  return `${sec}s`;
}
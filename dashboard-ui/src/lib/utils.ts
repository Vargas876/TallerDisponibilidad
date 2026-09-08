import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatTs(ts: number): string {
  const d = new Date(ts * 1000)
  return d.toLocaleTimeString("es-AR", { hour12: false }) + "." + String(d.getMilliseconds()).padStart(3, "0")
}
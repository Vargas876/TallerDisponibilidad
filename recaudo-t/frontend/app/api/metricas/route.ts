import { NextResponse } from "next/server";
import fs from "node:fs";
import path from "node:path";
import { METRICAS_E0, METRICAS_E1, fusionar } from "@/lib/defaultMetrics";
import type { Metricas } from "@/lib/types";

export const dynamic = "force-dynamic";

function raizRepo(): string {
  return path.resolve(process.cwd(), "..");
}

function leerMetricsLive(): Metricas | null {
  const dir = process.env.RESULTS_DIR
    ? path.isAbsolute(process.env.RESULTS_DIR)
      ? process.env.RESULTS_DIR
      : path.resolve(raizRepo(), process.env.RESULTS_DIR)
    : path.resolve(raizRepo(), "results");
  const ruta = path.join(dir, "metrics.json");
  try {
    if (!fs.existsSync(ruta)) return null;
    return JSON.parse(fs.readFileSync(ruta, "utf-8")) as Metricas;
  } catch {
    return null;
  }
}

export async function GET() {
  const live = leerMetricsLive();
  const payload = {
    fuente: live ? "live" : "incrustado",
    e0: fusionar(live?.experiment === "e0" ? live : null, METRICAS_E0),
    e1: fusionar(live?.experiment === "e1" ? live : null, METRICAS_E1),
  };
  return NextResponse.json(payload);
}
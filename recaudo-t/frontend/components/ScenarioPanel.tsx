"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import type { ReplicaState } from "@/lib/types";
import { DISPATCHER_URL } from "@/lib/useDispatcher";

type Estado = "idle" | "cargando" | "ok" | "error";

export function ScenarioPanel({ replicas }: { replicas: ReplicaState[] }) {
  if (!replicas?.length) return null;

  return (
    <motion.section
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.5, 0, 0.1, 1] }}
      className="card mb-6 px-4 py-4"
    >
      <div className="mb-3 flex items-baseline justify-between">
        <div>
          <p className="eyebrow mb-1">Escenarios del taller</p>
          <h2 className="text-lg font-semibold tracking-tight text-ink">
            Injecta una falla y obsérvala en vivo
          </h2>
        </div>
        <span className="mono-label text-faint hidden md:block">
          vía POST /chaos/* al dispatcher
        </span>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        {replicas.map((rep) => (
          <ScenarioRow key={rep.id} rep={rep} />
        ))}
      </div>

      <p className="mono-label mt-3 text-faint">
        E1 tumba la réplica (el monitor la marca CAÍDA en ~T·k y el tráfico lo
        cubren las demás). Q3 la deja "viva" para el ping pero con /saldo roto
        (500): el panel Resultados demuestra que la redundancia lo descarta. La
        réplica vuelve sola cuando Render la relanza (o redeployala).
      </p>
    </motion.section>
  );
}

function ScenarioRow({ rep }: { rep: ReplicaState }) {
  const caida = rep.status === "CAIDA";
  const [estado, setEstado] = useState<Estado>("idle");
  const [msj, setMsj] = useState("");

  async function ejecutar(accion: "crash" | "broken", body?: unknown) {
    setEstado("cargando");
    setMsj("");
    try {
      const res = await fetch(`${DISPATCHER_URL}/chaos/${accion}/${rep.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: body ? JSON.stringify(body) : undefined,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setEstado("ok");
      setMsj(
        accion === "crash"
          ? "CRASH enviado — mira el sello de detección"
          : `saldo roto ${data.activo ? "ON" : "OFF"}`,
      );
    } catch (e) {
      setEstado("error");
      setMsj("falló el disparo");
    }
    setTimeout(() => setEstado("idle"), 3000);
  }

  return (
    <div
      className={
        "rounded-lg border px-3 py-2 " +
        (caida ? "border-danger/40 bg-danger/5" : "border-faint/30")
      }
    >
      <div className="mb-2 flex items-center justify-between">
        <span className="num text-xl font-semibold tracking-tight text-ink">
          {rep.id}
        </span>
        <span
          className={
            "mono-label " + (caida ? "text-danger" : "text-ok")
          }
        >
          {rep.status}
        </span>
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => ejecutar("crash")}
          disabled={estado === "cargando"}
          className="px-3 py-1.5 text-[0.72rem] font-medium tracking-[0.15em] uppercase transition-colors border border-danger/45 bg-danger/15 text-danger hover:bg-danger/25 disabled:opacity-50"
        >
          {estado === "cargando" ? "…" : "Tumbar (E1)"}
        </button>
        <button
          type="button"
          onClick={() => ejecutar("broken", { activo: !rep.saldo_roto })}
          disabled={estado === "cargando" || caida}
          className="px-3 py-1.5 text-[0.72rem] font-medium tracking-[0.15em] uppercase transition-colors border border-faint/30 text-mut hover:border-line hover:text-ink disabled:opacity-50"
        >
          {rep.saldo_roto ? "Restaurar saldo" : "Saldo roto (Q3)"}
        </button>
      </div>

      {msj ? (
        <p className={"mono-label mt-2 " + (estado === "error" ? "text-danger" : "text-ok")}>
          {msj}
        </p>
      ) : null}
    </div>
  );
}
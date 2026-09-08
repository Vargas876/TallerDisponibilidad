"use client";

import { useEffect, useRef, useState } from "react";
import type { MensajeWs, PuntoSerie, Snapshot } from "@/lib/types";

export const DISPATCHER_URL =
  process.env.NEXT_PUBLIC_DISPATCHER_URL ?? "http://localhost:8000";

function eventosHaciaWs() {
  return DISPATCHER_URL.replace(/^http/, "ws") + "/ws";
}

interface UseDispatcher {
  snapshot: Snapshot | null;
  conectado: boolean;
  serie: PuntoSerie[];
  alarma: boolean;
  ultimoEvento: { replica: string; old: string; status: string; ts: number } | null;
  recientes: { ts: number; texto: string; tipo: string }[];
}

const INITIAL_SERIE = Array.from({ length: 60 }, (_, i) => ({ seg: i - 59, ok: 0, fail: 0 }));

export function useDispatcher(): UseDispatcher {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [conectado, setConectado] = useState(false);
  const [serie, setSerie] = useState<PuntoSerie[]>(INITIAL_SERIE);
  const [alarma, setAlarma] = useState(false);
  const [ultimoEvento, setUltimoEvento] = useState<UseDispatcher["ultimoEvento"]>(null);
  const [recientes, setRecientes] = useState<UseDispatcher["recientes"]>([]);

  const refs = useRef({
    acumOk: 0,
    acumFail: 0,
    ultimoTick: 0,
    serieInterna: [...INITIAL_SERIE],
  });

  useEffect(() => {
    let cerrado = false;
    let ws: WebSocket | null = null;
    let intentos = 0;

    function consumir(sn: Snapshot) {
      const r = refs.current;
      const ok = sn.replicas.reduce((a, b) => a + b.successful_requests, 0);
      const fail = sn.replicas.reduce((a, b) => a + b.failed_requests, 0);
      const ahora = Math.floor(Date.now() / 1000);

      if (r.ultimoTick === 0) {
        r.ultimoTick = ahora - 1;
      }
      const segFaltantes = Math.min(ahora - r.ultimoTick, 30);
      for (let i = 0; i < segFaltantes; i++) {
        r.serieInterna.push({ seg: r.ultimoTick + i + 1, ok: 0, fail: 0 });
      }
      if (r.serieInterna.length > 60) {
        r.serieInterna = r.serieInterna.slice(-60);
      }

      const last = r.serieInterna[r.serieInterna.length - 1];
      const dOk = Math.max(0, ok - r.acumOk);
      const dFail = Math.max(0, fail - r.acumFail);
      if (last && last.seg === ahora) {
        last.ok += dOk;
        last.fail += dFail;
      } else if (dOk > 0 || dFail > 0) {
        r.serieInterna.push({ seg: ahora, ok: dOk, fail: dFail });
        if (r.serieInterna.length > 60) r.serieInterna = r.serieInterna.slice(-60);
      }
      r.acumOk = ok;
      r.acumFail = fail;
      r.ultimoTick = ahora;

      setSnapshot(sn);
      setSerie([...r.serieInterna]);
      const caida = sn.replicas.filter((x) => x.status === "CAIDA").length;
      setAlarma(caida > 0);
    }

    function conectar() {
      if (cerrado) return;
      ws = new WebSocket(eventosHaciaWs());
      ws.onopen = () => {
        intentos = 0;
        setConectado(true);
      };
      ws.onmessage = (ev) => {
        try {
          const m = JSON.parse(ev.data) as MensajeWs;
          if (m.type === "hello" || m.type === "snapshot") {
            const sn: Snapshot = {
              version: m.version ?? "RECAUDO-T/1.0",
              disponible: Boolean(m.disponible),
              replicas_viva: m.replicas_viva ?? 0,
              replicas: m.replicas ?? [],
              total_solicitudes: m.total_solicitudes ?? 0,
              last_detection: m.last_detection ?? null,
              uptime_s: m.uptime_s ?? 0,
            };
            consumir(sn);
          } else if (m.type === "replica_status_changed") {
            setUltimoEvento({ replica: m.replica, old: m.old, status: m.status, ts: m.ts });
            const tipo = m.status === "CAIDA" ? "down" : "up";
            setRecientes((prev) =>
              [
                {
                  ts: m.ts,
                  texto: `REPLICA_${m.replica} ${m.old} → ${m.status}`,
                  tipo,
                },
                ...prev,
              ].slice(0, 12),
            );
          }
        } catch {
          /* mensaje no parseable */
        }
      };
      ws.onclose = () => {
        setConectado(false);
        if (!cerrado) {
          intentos += 1;
          setTimeout(conectar, Math.min(1500 * intentos, 8000));
        }
      };
      ws.onerror = () => ws?.close();
    }

    conectar();
    return () => {
      cerrado = true;
      ws?.close();
    };
  }, []);

  return { snapshot, conectado, serie, alarma, ultimoEvento, recientes };
}
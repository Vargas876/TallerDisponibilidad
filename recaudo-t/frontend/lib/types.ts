export type EstadoReplica = "VIVA" | "CAIDA";

export interface ReplicaState {
  id: string;
  url: string;
  status: EstadoReplica;
  consecutive_failures: number;
  consecutive_successes: number;
  last_ping: number | null;
  latency_ms: number | null;
  last_ok: number | null;
  last_down: number | null;
  last_up: number | null;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  last_error: string | null;
  saldo_roto: boolean;
  disponible: boolean;
}

export interface Snapshot {
  version: string;
  disponible: boolean;
  replicas_viva: number;
  replicas: ReplicaState[];
  total_solicitudes: number;
  last_detection: { replica: string; at: number } | null;
  uptime_s: number;
}

export type MensajeWs =
  | ({ type: "hello" | "snapshot" } & Partial<Snapshot>)
  | {
      type: "replica_status_changed";
      replica: string;
      old: string;
      status: string;
      ts: number;
    };

export interface PuntoSerie {
  seg: number;
  ok: number;
  fail: number;
}

export interface Metricas {
  experiment: string;
  fecha: number;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  success_rate: number;
  latency_mean_ms: number | null;
  distribucion_por_replica: Record<string, number>;
  serie_por_segundo: PuntoSerie[];
  inyeccion?: { ts: number; replica: string };
  deteccion?: { ts: number; tiempo_s: number; replica: string };
  recuperacion?: { ts: number; tiempo_s: number; replica: string };
}
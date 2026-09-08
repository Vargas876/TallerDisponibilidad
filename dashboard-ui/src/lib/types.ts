export type ReplicaState = string

export interface EstadoInfo {
  estado: Record<string, ReplicaState>
  total_solicitudes: number
}

export interface ApiEstado {
  disponible: boolean
  estado?: EstadoInfo
}

export interface BitacoraLine {
  ts: number
  texto: string
  tipo: "caida" | "viva" | "info"
}

export interface ApiBitacora {
  lineas: string[]
}

export interface InyectorInfo {
  timestamp?: number
  replica?: string
}

export interface PuntoSerie {
  seg: number
  ok: number
  fail: number
}

export interface ResultadoProcesado {
  archivo: string
  total: number
  exitosos: number
  fallidos: number
  porcentaje: number
  replicas: Record<string, number>
  serie: PuntoSerie[]
}

export interface ApiResultados {
  archivos: string[]
}
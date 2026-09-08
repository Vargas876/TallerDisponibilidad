import type { ApiEstado, ApiBitacora, InyectorInfo, ResultadoProcesado, ApiResultados } from "./types"

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return (await res.json()) as T
}

export function getEstado(): Promise<ApiEstado> {
  return fetchJson<ApiEstado>("/api/estado")
}

export function getBitacora(): Promise<ApiBitacora> {
  return fetchJson<ApiBitacora>("/api/bitacora")
}

export function getInyector(): Promise<InyectorInfo> {
  return fetchJson<InyectorInfo>("/api/inyector")
}

export function getResultados(): Promise<ApiResultados> {
  return fetchJson<ApiResultados>("/api/resultados")
}

export function getResultado(archivo: string): Promise<ResultadoProcesado> {
  return fetchJson<ResultadoProcesado>(`/api/resultado?archivo=${encodeURIComponent(archivo)}`)
}
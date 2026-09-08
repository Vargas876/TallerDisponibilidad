import type { QaItem } from "@/components/QaPanel";

export const PREGUNTAS: QaItem[] = [
  {
    q: "¿Cuánto tarda el sistema en detectar la caída de una réplica?",
    a: [
      "La detección usa Ping/Echo con período T=1s, timeout t=0.3s y umbral k=2 fallos consecutivos: tiempo de detección estructural T·k ≈ 2s.",
      "En el experimento E1 el Ping/Echo detectó la caída de la réplica B en 2.139s desde la inyección del CRASH.",
    ],
    evidencia: "e1.deteccion.tiempo_s = 2.139s ≤ 3s requerido",
  },
  {
    q: "¿El sistema continúa respondiendo durante la ventana de detección?",
    a: [
      "Sí. El dispatcher aplica redundancia activa: cada solicitud se lanza en paralelo a todas las réplicas marcadas VIVA y se devuelve la primera respuesta válida.",
      "Incluso mientras una réplica está muerta pero aún no detectada, las peticiones son atendidas por las réplicas vivas restantes: 100% de solicitudes exitosas en E1 a pesar de la caída.",
    ],
    evidencia: "e1.success_rate = 100% · failed_requests = 0",
  },
  {
    q: "¿Qué ocurre si una réplica responde al ping pero devuelve saldos rotos?",
    a: [
      "El Ping/Echo solo mide disponibilidad de red; la integridad de datos se valida en la capa de redundancia: a una réplica con fallo de saldo se la retira del fan-out y atienden las demás.",
      "El escenario se construye con REPLICA_BROKEN_SALDO: la réplica pasa pings pero sus respuestas son descartadas y no se entregan al cliente.",
      "Medición Q3: 160/160 solicitudes exitosas (100%), réplica B marcada VIVA por el monitor pero con 0 saldos exitosos y 148 intentos fallidos descartados.",
    ],
    evidencia: "results/q3.json · REPLICA_BROKEN_SALDO · conteos failed/successful por réplica",
  },
  {
    q: "¿La redundancia activa enmascara los fallos frente al cliente?",
    a: [
      "Sí, y es medible: durante la ventana previa a la detección los intentos hacia la réplica caída fallan internamente (contador failed_requests) pero el cliente jamás los percibe.",
      "En E1 la réplica B acumuló intentos fallidos mientras seguía nominalmente VIVA, sin una sola petición fallida observada por el cliente (800/800 exitosas).",
    ],
    evidencia: "distribucion_por_replica: B atendió 197 solicitudes exitosas antes de caer y tras restablecerse · fallos enmascarados en bitácora",
  },
  {
    q: "¿Cómo afecta la caída y recuperación al reparto y la latencia?",
    a: [
      "El reparto es proporcionado mientras todas las réplicas están VIVA (E0: A 320 / B 286 / C 194). Al caer B, los nuevos tráficos se reparten entre las vivas y el trabajo pendiente de B se cancela.",
      "La latencia media se mantiene plana: E0 214.2ms vs E1 219.4ms. La consulta en paralelo con cancelación (FIRST_COMPLETED) evita esperar réplicas lentas.",
    ],
    evidencia: "latency_mean_ms e0=214.18 · e1=219.41 · distribución en metrics.json",
  },
];
import type { QaItem } from "@/components/QaPanel";

export const PREGUNTAS: QaItem[] = [
  {
    q: "P1 · En E1, ¿el cliente dejó de recibir respuesta antes o después de que el monitor detectara la caída? ¿Por qué y qué revela de la relación entre Ping/Echo y redundancia activa?",
    a: [
      "El cliente jamás dejó de recibir respuesta: las 800 solicitudes de E1 fueron exitosas (exito=1 en el CSV). La caída se registró en la bitácora 2.139s después de la inyección, pero durante esa ventana el dispatcher ya enviaba cada consulta, en paralelo, a todas las réplicas marcadas VIVA (incluida B todavía 'viva'), y respondía con la primera válida: ganaban A o C.",
      "Esto muestra que las dos tácticas son complementarias: la redundancia protege al cliente mientras el monitor detecta; si el fan-out esperara a la detección, habría errores durante esos ~2s.",
    ],
    evidencia: "results/e1.csv · 800 filas exito=1 · monitor.log: inyección 1788884337.965 → VIVA→CAÍDA 1788884340.104 (2.139s)",
  },
  {
    q: "P2 · Si solo hubiera Ping/Echo (sin redundancia), ¿el usuario habría notado la falla? ¿Y solo redundancia sin monitor, para qué serviría entonces el monitor?",
    a: [
      "Con solo Ping/Echo el usuario notaría la falla: sin réplicas extra a quien reenviar, las consultas durante la ventana de detección y tras confirmar la caída terminarían en error o en esperas que agotan el timeout. El monitor solo informa: no atiende consultas.",
      "Con solo redundancia, el usuario no notaría la falla (las réplicas vivas lo absorben todo), pero nadie sabría que B sigue muerta: la bitácora de cambios, el estado y las alarmas que usa el operador simplemente no existirían. El monitor aporta la visibilidad y el registro que convierten una caja negra en un sistema diagnosticable.",
    ],
    evidencia: "monitor.log: [ts] REPLICA_X VIVA→CAÍDA y CAÍDA→VIVA en cada transición · /estado refleja VIVA/CAÍDA en vivo",
  },
  {
    q: "P3 · Si una réplica responde /ping pero devuelve un saldo incorrecto, ¿el monitor lo detectaría? ¿Por qué no, y qué táctica adicional ayudaría?",
    a: [
      "No lo detectaría. /ping solo verifica alcanzabilidad y tiempo de eco: mide disponibilidad de red, no integridad de los datos. Un saldo roto es una falla lógica que deja la red intacta, por lo que el monitor seguiría viendo pings OK y la réplica quedaría VIVA.",
      "La táctica que lo cubre es la verificación de integridad en la capa de respuesta redundante: contrastar el cuerpo de las respuestas entre réplicas (votación) o validar contra una fuente de verdad. Se midió en el escenario Q3: la réplica B respondía /ping normal (para el monitor seguía VIVA) pero con REPLICA_BROKEN_SALDO el dispatcher descartaba sus respuestas: 148 intentos fallidos internos, 0 entregados, y 160/160 solicitudes correctas.",
    ],
    evidencia: "results/q3.json · REPLICA_BROKEN_SALDO · conteos failed/successful por réplica (B: 0 exitosos / 148 descartados)",
  },
  {
    q: "P4 · Con disponibilidad individual 0.98 y fallas independientes, calcule la del sistema con 2 y con 3 réplicas bajo redundancia activa. ¿Cuándo es falso el supuesto de independencia?",
    a: [
      "Con redundancia activa el sistema sirve si al menos una réplica está viva, así que la indisponibilidad conjunta es el producto de las indisponibilidades individuales. Con 2 réplicas: 1 − (1−0.98)² = 1 − 0.0004 = 0.9996 (99.96%). Con 3 réplicas: 1 − (1−0.98)³ = 1 − 0.000008 = 0.999992 (99.9992%). Cada réplica adicional multiplica la mejora.",
      "El supuesto de independencia se rompe cuando las réplicas comparten un modo de falla común: mismo host físico o vSwitch, misma versión de software con el mismo bug, mismo plan de actualización, misma fuente de alimentación o el mismo dispatcher. En fallas correlacionadas la disponibilidad conjunta no mejora con más réplicas.",
    ],
    evidencia: "E0 responde con 3 réplicas distintas (A 320 · B 286 · C 194) · fallas operativas compartidas no modeladas por p>0.98",
  },
  {
    q: "P5 · El dispatcher es ahora el único punto por el que circula todo el tráfico: ¿introdujo un nuevo punto único de falla al resolver el anterior?",
    a: [
      "Sí: se transfirió el riesgo. La arquitectura elimina el SPOF de la instancia de saldo, pero concentra todo el tráfico en el dispatcher; si un dispatcher cae, la conclusión es la misma que en el arranque del problema: nadie consulta saldo. Su disponibilidad es ahora multiplicadora de la del resto del sistema.",
      "Mitigaciones: tratar al dispatcher igual que a las réplicas — someterlo al propio Ping/Echo (La vista Live lo monitorea vía /estado y websocket), desplegarlo como servicio replicado y stateless al menos en activo/activo para que la redundancia quede completa en toda la cadena.",
    ],
    evidencia: "/estado y /ws del dispatcher expuestos y observables en Live · uptime_s · disponible",
  },
];
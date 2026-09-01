# Plan de Implementación — Taller Disponibilidad II

## Visión general del sistema

El sistema simula **RECAUDO-T**, un servicio de consulta de saldo para transporte masivo. Implementa dos tácticas de disponibilidad:

| Táctica | Función |
|---|---|
| **Ping/Echo** | Detección de fallas mediante sondeo periódico |
| **Redundancia Activa** | Recuperación instantánea usando múltiples réplicas en paralelo |

### Componentes del sistema

```
┌─────────────┐
│   CLIENTE   │ ← Script que genera carga (20 req/s, 40s)
└──────┬──────┘
       │ GET /saldo/{id}
       ▼
┌─────────────┐
│ DISPATCHER  │ ← Hilo 1: sondeo Ping/Echo cada T s
│  (puerto    │ ← Hilo 2: atiende consultas
│   fijo)     │ ← GET /estado
└──────┬──────┘
       │ envía a todas las réplicas VIVA
       ▼
┌──────┴──────────────────────┐
│                             │
▼              ▼              ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│REPLICA A│ │REPLICA B│ │REPLICA C│
└─────────┘ └─────────┘ └─────────┘
GET /ping       GET /ping       GET /ping
GET /saldo      GET /saldo      GET /saldo
POST /chaos     POST /chaos     POST /chaos

       ▲
       │ POST /chaos/crash
┌──────┴──────┐
│  INYECTOR   │ ← Script manual que mata una réplica
└─────────────┘
```

---

## Fase 0: Estructura del proyecto

```
TallerDisponibilidad/
├── config.json                  # Parámetros configurables (T, t, k, réplicas, puertos)
├── replica.py                   # Servidor HTTP de cada réplica
├── dispatcher.py                # Dispatcher: Ping/Echo + redirección de consultas
├── client.py                    # Generador de carga → CSV
├── inyector.py                  # Script para matar réplicas
├── requirements.txt             # Dependencias Python
├── bitacora_monitor.log         # Log del monitor (generado en runtime)
├── resultados/                  # CSVs de cada corrida
│   ├── E0.csv
│   └── E1_run1.csv
└── PLAN_IMPLEMENTACION.md       # Este archivo
```

**Lenguaje recomendado:** Python 3 (asyncio + aiohttp o httpx). Es simple, tiene bibliotecas HTTP asíncronas nativas, y corre en cualquier SO.

---

## Fase 1: Configuración centralizada

Crear `config.json` con los parámetros del enunciado:

```json
{
  "T": 1,
  "t": 0.3,
  "k": 2,
  "num_replicas": 3,
  "base_port": 5001,
  "dispatcher_port": 5000,
  "client_duration": 40,
  "client_rate": 20,
  "failure_inject_at_second": 15
}
```

- **T** = intervalo de sondeo (s)
- **t** = timeout por sondeo (s)
- **k** = fallos consecutivos para marcar CAÍDA
- **num_replicas** = cantidad de réplicas (sin modificar código)
- **base_port** = puerto de la primera réplica (5001, 5002, ...)

---

## Fase 2: Réplica (`replica.py`)

**Cada réplica es un proceso independiente** que recibe su ID y puerto por argumento o variable de entorno.

### Endpoints

| Método | Ruta | Comportamiento |
|---|---|---|
| `GET` | `/ping` | Retorna `{"replica_id": "A"}` con código 200 en < t |
| `GET` | `/saldo/{id}` | Retorna `{"replica_id": "A", "saldo": 15000}` con código 200 |
| `POST` | `/chaos/crash` | `sys.exit(0)` — termina el proceso |

### Puntos clave

- Cada réplica se ejecuta como un **proceso separado**: `python replica.py --id A --port 5001`
- El endpoint `/chaos/crash` mata el proceso inmediatamente (no necesita delay)
- El saldo devuelto puede ser un valor fijo o calculado con hash del `id` para consistencia

---

## Fase 3: Dispatcher (`dispatcher.py`) — El componente más complejo

### Hilo 1: Monitor Ping/Echo (detección)

```python
# Pseudocódigo del ciclo de sondeo
while True:
    for replica in replicas:
        try:
            response = await http_get(f"http://{replica.host}:{replica.port}/ping", timeout=t)
            if replica.fallos_consecutivos >= k:
                log(f"[{timestamp}] {replica.id} CAÍDA → VIVA")  # recuperación
            replica.fallos_consecutivos = 0
            replica.estado = "VIVA"
        except (TimeoutError, ConnectionError):
            replica.fallos_consecutivos += 1
            if replica.fallos_consecutivos == k:
                replica.estado = "CAÍDA"
                log(f"[{timestamp}] {replica.id} VIVA → CAÍDA")
    await sleep(T)
```

### Hilo 2: Atención de consultas (redundancia activa)

```python
# Pseudocódigo del handler de /saldo
async def handle_saldo(id):
    réplicas_vivas = [r for r in replicas if r.estado == "VIVA"]
    
    tasks = [http_get(f"http://{r.host}:{r.port}/saldo/{id}") for r in réplicas_vivas]
    
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    
    for task in pending:
        task.cancel()  # descartar respuestas restantes
    
    return done.pop().result()  # primera respuesta válida
```

### Endpoints del dispatcher

| Método | Ruta | Comportamiento |
|---|---|---|
| `GET` | `/saldo/{id}` | Envía a réplicas VIVA en paralelo, retorna primera respuesta |
| `GET` | `/estado` | Retorna JSON con estado de todas las réplicas |

### Concurrencia

- **asyncio** para ambos hilos (no bloquean entre sí)
- El sondeo se ejecuta en un `asyncio.Task` independiente
- Las consultas se atienden en otro `asyncio.Task`
- **No hay bloqueo cruzado** entre sondeo y atención de consultas

---

## Fase 4: Cliente (`client.py`)

Genera carga constante y registra todo en CSV.

### Comportamiento

```
while elapsed < DURACION:
    timestamp_envio = now()
    try:
        response = http_get(f"http://{dispatcher}/saldo/1234")
        exito = 1
        replica = response.json()["replica_id"]
    except:
        exito = 0
        replica = None
    timestamp_respuesta = now()
    
    writer.writerow([timestamp_envio, timestamp_respuesta, exito, replica])
    
    sleep(1 / RATE)  # mantener tasa constante
```

### CSV de salida

| timestamp_envio | timestamp_respuesta | exito | replica |
|---|---|---|---|
| 1690000000.000 | 1690000000.045 | 1 | B |
| 1690000000.050 | 1690000000.310 | 1 | A |

---

## Fase 5: Inyector de fallas (`inyector.py`)

Script manual que ejecuta el usuario en una terminal separada:

```python
import requests, time, subprocess, sys

replica_id = sys.argv[1]  # "A", "B", o "C"
port = 5001 + ord(replica_id) - ord("A")

print(f"[{time.time()}] Inyectando falla en réplica {replica_id}...")
requests.post(f"http://localhost:{port}/chaos/crash")
print(f"[{time.time()}] Réplica {replica_id} eliminada")
```

**Nota:** El `POST /chaos/crash` mata el proceso desde dentro. Alternativa: usar `kill -9 <pid>` si se conoce el PID.

---

## Fase 6: Experimentos

### E0 — Línea base (sin fallas)

```bash
# Terminal 1: réplicas
python replica.py --id A --port 5001
python replica.py --id B --port 5002
python replica.py --id C --port 5003

# Terminal 2: dispatcher
python dispatcher.py

# Terminal 3: cliente (40 segundos)
python client.py --output resultados/E0.csv

# Verificar: columnas "replica" muestran A, B, C alternándose
```

### E1 — Caída abrupta (con inyector)

```bash
# Mismos pasos que E0, pero a los 15 segundos:
# Terminal 4:
python inyector.py B

# Verificar:
# 1. bitacora_monitor.log → timestamp de VIVA → CAÍDA de B
# 2. CSV → pocas o ninguna fila con exito=0
# 3. GET /estado → B aparece como CAÍDA
```

### Cálculos de métricas

| Métrica | Fórmula |
|---|---|
| Tiempo de detección | `timestamp_log(VIVA→CAÍDA) - timestamp_inyector` |
| % éxito total | `filas(exito=1) / total_filas` |
| % éxito durante caída | `filas(exito=1, ventana) / filas(ventana)` |

---

## Fase 7: Entregables

| # | Entregable | Archivo |
|---|---|---|
| 1 | Código fuente + instrucciones | `*.py` + `README.md` |
| 2 | Bitácora + CSV de E1 | `bitacora_monitor.log` + `resultados/E1.csv` |
| 3 | Tabla de métricas | En `RESULTADOS.md` |
| 4 | Análisis de las 5 preguntas | En `RESULTADOS.md` |

---

## Orden de implementación recomendado

```
1. config.json
2. replica.py (probar con curl: GET /ping, GET /saldo, POST /chaos)
3. dispatcher.py — hilo de sondeo Ping/Echo (probar con GET /estado)
4. dispatcher.py — handler de /saldo con redundancia activa
5. client.py (probar que genera CSV correcto)
6. inyector.py (probar que mata una réplica)
7. Experimento E0 → verificar alternancia
8. Experimento E1 → medir detección y éxito
9. Documentar resultados y responder preguntas
```

---

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Dispatcher se vuelve SPOF | Mencionar en análisis (pregunta 5); no resolver en este taller |
| Réplica no muere con `/chaos/crash` | Usar `os._exit(0)` en vez de `sys.exit()` para forzar terminación |
| Conflicto de puertos entre corridas | Agregar flag `--run-id` al cliente para separar CSVs |
| Timeout muy bajo causa falsos positivos | Empezar con `t=0.3` (300ms), subir si hay mucha falsa alarma |

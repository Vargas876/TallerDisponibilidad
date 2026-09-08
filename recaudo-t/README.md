# RECAUDO-T — Availability & Resilience Monitor

Taller de **disponibilidad y tolerancia a fallos** de un sistema de consulta de
saldos.

Una aplicación de saldos deterministas se ejecuta en réplicas redundantes
detrás de un **dispatcher** que aplica **redundancia activa** (fan-out paralelo,
primera respuesta válida) y supervisa la salud de cada réplica con un monitor
**Ping/Echo** (T, t, k). El taller mide con experimentos controlados:

- **E0** — operación normal: disponibilidad del sistema con todas las réplicas VIVA.
- **E1** — inyección de falla: CRASH contra la réplica **B** y recuperación; mide
  latencia de detección y de reincorporación.
- **Q3** — fallo de integridad (saldo roto con ping OK): limitación del Ping/Echo
  cubierta por la validación en la capa de redundancia.
- Un **frontend premium** (Next.js) que visualiza el sistema en vivo y los
  resultados medidos, desplegable a Vercel.

---

## 1. Resultados medidos (corridas finales, CLIENT_RATE=20 req/s × 40 s)

| Métrica | E0 (sin fallas) | E1 (falla B en t+15s) |
|---|---|---|
| Solicitudes | 800 | 800 |
| Exitosas / fallidas | 800 / 0 | 800 / 0 |
| Tasa de éxito | **100 %** | **100 %** |
| Latencia media | 214.18 ms | 219.41 ms |
| Distribución | A 320 · B 286 · C 194 | A 347 · B 197 · C 256 |
| Detección de caída | — | **2.139 s** (≤ 3 s) |
| Recuperación (tras detección) | — | +5.763 s |

**Escenario Q3** (saldo roto): 160/160 (100 %) exitosas; la réplica B quedó
**VIVA** para el Ping/Echo pero con **0 saldos exitosos** y 148 intentos
descartados por la redundancia. Evidencia en `results/q3.json`.

Todas las bitácoras, CSVs y `metrics.json` quedan en `results/` y `logs/`.

### Preguntas del taller (Q1–Q5)

1. **¿Cuánto tarda en detectar una caída?** Estructura T=1s, t=0.3s, k=2 ⇒
   T·k ≈ 2 s. Medido: **2.139 s** desde el CRASH (≤ 3 s requerido).
2. **¿Continúa respondiendo durante la ventana de detección?** Sí: redundancia
   activa atiende con las réplicas vivas y cancela las muertas. 100 % en E1.
3. **¿Qué pasa si el ping pasa pero el saldo es inválido?** El monitor no lo ve,
   pero la capa de redundancia descarta la respuesta corrupta (Q3 verificado).
4. **¿La redundancia enmascara los fallos?** Sí: contadores internos de
   `failed_requests` crecen mientras el cliente ve 0 fallos.
5. **¿Cómo afecta el reparto y la latencia?** Reparto proporcional mientras
   todas viven; latencia estable (FIRST_COMPLETED + cancelación).

---

## 2. Arquitectura

```
                    ┌──────────────────────────────────────────────┐
                    │             DISPATCHER (:8000) ✦ monitor      │
   cliente ───────▶ │  /saldo/{tarjeta}  redundancia activa          │
 (20 req/s)         │  /estado  estado y contadores por réplica      │
                    │  /ws      telemetría en vivo (WebSocket)       │
                    │  Ping/Echo cada T=1s → decide VIVA/CAÍDA        │
                    └───┬───────────┬───────────┬───────────────────┘
                        │ ping/echo │           │
                 replica-a:8001 ┌───┴─┐ replica-c:8003
                     replica-b:8002  (3 réplicas /saldo, /ping, /chaos/crash)
```

- **Réplica (`backend/replica/`)** — contrato de saldo determinístico por
  tarjeta (`sha256(REPLICA_ID:tarjeta)`), `/ping`, `/saldo/{id}`,
  `/chaos/crash` (suicidio para inyección) y modo `REPLICA_BROKEN_SALDO`.
- **Dispatcher (`backend/dispatcher/`)** — estado por réplica (Ping/Echo con
  umbrales T/t/k), **redundancia activa**: cada solicitud se dispara en paralelo
  a todas las réplicas VIVA y se **devuelve la primera respuesta válida**,
  cancelando el resto (`asyncio.wait` FIRST_COMPLETED). Bitácora con
  transiciones `VIVA → CAÍDA` / `CAÍDA → VIVA` en `logs/monitor.log`.
- **Cliente (`backend/client/`)** — carga con ritmo fijo y CSV de evidencias
  (exito, latencia, réplica atendida).
- **Inyector (`backend/injector/`)** — fuerza un CRASH (`/chaos/crash`) con
  timestamp para anclar la medición de detección.
- **Métricas (`backend/metrics.py`)** — consolida CSV + bitácora en
  `results/metrics.json` (serie por segundo, latencia, detección, recuperación).
- **Orquestador (`scripts/run_experiment.py`)** — levanta réplicas+dispatcher
  (local o Docker), ejecuta cliente, inyecta en E1, reinicia la réplica para
  evidenciar recuperación y computa métricas.
- **Frontend (`frontend/`)** — Next.js 16 + React 19 + Tailwind 4: **Live**
  (KPIs, estado de réplicas, tráfico en tiempo real vía WebSocket, Detection
  Stamp y línea de tiempo) y **Resultados** (gráficas E0/E1 con bandas de
  inyección/detección/recuperación y las respuestas Q1–Q5).

---

## 3. Configuración

`config/.env` (sobreescribible por variables de entorno):

| Variable | Default | Descripción |
|---|---|---|
| `PING_INTERVAL` (T) | `1` | período del Ping/Echo (s) |
| `PING_TIMEOUT` (t) | `0.3` | timeout por ping (s) |
| `FAILURE_THRESHOLD` (k) | `2` | fallos consecutivos ⇒ CAÍDA |
| `RECOVERY_THRESHOLD` | `2` | éxitos consecutivos ⇒ VIVA |
| `CLIENT_RATE` | `20` | peticiones por segundo |
| `EXPERIMENT_DURATION` | `40` | duración del cliente (s) |
| `FAILURE_INJECT_AT` | `15` | segundo de inyección en E1 |
| `TARGET_REPLICA` | `B` | réplica a fallar |
| `RECOVERY_DELAY` | `5` | espera antes del reinicio (s) |
| `NUM_REPLICAS` | `3` | réplicas locales |
| `REPLICA_BASE_PORT` | `8001` | puerto base de réplicas |
| `DISPATCHER_PORT` | `8000` | puerto del dispatcher |
| `REPLICA_*_URL` | — | URLs (Docker usa nombres de servicio) |
| `REPLICA_BROKEN_SALDO` | `0` | escenario Q3 (saldo roto) |

---

## 4. Instalación y uso

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd frontend; npm install; cd ..

# Entorno local (replicas + dispatcher + Next dev)
.\.venv\Scripts\python.exe scripts\dev_local.py        # Ctrl+C detiene y limpia
& .\.venv\Scripts\python.exe scripts\smoke_live.py     # prueba E2E completa

# Experimentos (local)
.\.venv\Scripts\python.exe scripts\run_experiment.py e0
.\.venv\Scripts\python.exe scripts\run_experiment.py e1

# Escenario Q3
.\.venv\Scripts\python.exe scripts\scenario_q3.py
```

O vía Make (`make install/up/dev/e0/e1/q3/smoke` — en Windows usa Git Bash/msys2).

### Docker

```bash
docker compose up -d --build dispatcher replica-a replica-b replica-c frontend
python scripts/run_experiment.py e0 --mode docker   # cliente/inyector/métricas en contenedores
python scripts/run_experiment.py e1 --mode docker
open http://localhost:3000
```

- `docker-compose.yml` define los servicios de runtime y los servicios
  "tools" (`client`, `injector`, `metrics`, perfil `tools`) que el orquestador
  invoca con `docker compose run --rm --no-deps`.
- `logs/` y `results/` son volúmenes hacia el host para inspeccionar evidencias.
- Nota: `frontend/Dockerfile` usa `npm install` (el lock de plataforma win32
  omite dependencias opcionales musl/alpine y `npm ci` las rechaza).

---

## 5. Despliegue en vivo

Frontend **Vercel**: https://recaudo-t-frontend.vercel.app \
Backend **Render** (blueprint `render.yaml`, raíz del repo):

- dispatcher:  https://recaudo-t-dispatcher.onrender.com
- réplicas:    https://recaudo-t-replica-a.onrender.com  https://recaudo-t-replica-b.onrender.com  https://recaudo-t-replica-c.onrender.com

`frontend/.env.production` fija `NEXT_PUBLIC_DISPATCHER_URL` al dispatcher de
Render para que la vista **Live** funcione punta a punta (`wss://.../ws`).

Build/uso:
1. El blueprint despliega los 4 services (docker, entrypoint por `REPLICA_ID`);
   cualquier push a `main` los re-despliega (`autoDeploy: true`).
2. **Resultados** usa las métricas embebidas (regenerables con
   `python scripts/rebuild_defaults.py`) — verifica `fuente: incrustado` en
   `/api/metricas`; con dispatcher local la fuente es `live`.
3. Caveat free tier: Render duerme las réplicas tras ~15 min de inactividad
   (la monkeytype muestra "canal caído" hasta que un request/WS las despierta);
   para demo continua usar plan `starter`.

`scripts/rebuild_defaults.py` regenera `frontend/lib/defaultMetrics.ts` desde
los resultados finales para que el despliegue muestre las cifras medidas.

---

## 6. Estructura

```
config/.env                configuración del taller
backend/
  dispatcher/              dispatcher + monitor Ping/Echo + websocket
  replica/                 réplica de saldo (/ping /saldo /chaos/crash)
  client/client.py         carga y CSV de evidencias
  injector/injector.py     inyección de CRASH
  metrics.py               consolidación → results/metrics.json
scripts/
  run_experiment.py        orquestador E0/E1 (local|docker)
  scenario_q3.py           escenario de saldo roto → results/q3.json
  smoke_live.py            prueba punta a punta (pila + frontend + WS)
  dev_local.py             pila local en primer plano
  rebuild_defaults.py      regenera métricas embebidas del frontend
frontend/                  Next.js 16 (Live + Resultados) — desplegable
results/                   CSVs, q3.json, injection_e1.log, metrics.json
logs/monitor.log           bitácora con transiciones VIVA↔CAÍDA
docker-compose.yml         pila Docker + servicios tools
Makefile                   alias de tareas
```

---

## 7. Supuestos y límites

- El Ping/Echo mide **disponibilidad de red/de proceso**, no integridad de
  datos: un fallo lógico (Q3) se detecta en la capa de redundancia, no en el
  monitor (métricas de B lo reflejan).
- La redundancia activa enmascara fallos frente al cliente por diseño; la
  evidencia de degradación queda en los contadores internos y la bitácora
  (Q4).
- Umbrales T=1s / k=2 dan detección estructural ≈ 2 s; bajar k acelera a costa
  de falsos positivos.
- En `--mode docker` el orquestador no reinicia la réplica caída (E1 Docker
  documenta la detección; la recuperación se evidencia en modo local con el
  reinicio automático).
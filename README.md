# Taller Disponibilidad II — Ping/Echo + Redundancia Activa

## Requisitos
- Python 3.7 o superior (solo stdlib)
- Node.js 18+ y npm (solo para compilar el dashboard React, una sola vez)

## Ejecución rápida

```bash
python run.py
```

Este comando:
1. Levanta 3 réplicas (puertos 5001, 5002, 5003)
2. Levanta el dispatcher (puerto 5000)
3. Levanta el dashboard web (puerto 8000)
4. Ejecuta el cliente durante 40 segundos
5. Inyecta una falla en la réplica B a los 15 segundos
6. Genera los archivos de resultados

## Dashboard web (profesional — React + shadcn/ui)

El dashboard es una SPA **React + TypeScript + Tailwind v4 + shadcn/ui + Recharts**
con sidebar, KPIs con tonos, réplicas en vivo, bitácora con búsqueda/filtros y
vista de resultados con gráficas.

Compilar el frontend (requiere Node, se hace una vez):

```bash
cd dashboard-ui
npm install
npm run build
cd ..
```

Levantar (durante o después del experimento):

```bash
python dashboard.py
```

Abrir http://127.0.0.1:8000

- **En vivo**: estado de cada réplica (VIVA/CAÍDA, tarjetas con glow), KPIs,
  bitácora del monitor en tiempo real con buscador y filtros por tipo de evento,
  y datos de la última inyección de falla.
- **Resultados**: selector de CSV (E0/E1/E2…), total/éxitos/fallos/% de éxito,
  gráfica de solicitudes por segundo (éxitos vs fallos), distribución por
  réplica y checklist de verificación del experimento.
- Para desarrollo con hot-reload: `cd dashboard-ui && npm run dev` (http://127.0.0.1:5173).
- **API JSON** del backend en el mismo origen: `/api/estado`, `/api/bitacora`,
  `/api/inyector`, `/api/resultados`, `/api/resultado?archivo=...`.

> Si `dashboard-ui/dist` no existe, `dashboard.py` sirve un fallback HTML simple.

## Archivos generados
- `bitacora_monitor.log` — Log del monitor Ping/Echo
- `resultados/E1.csv` — CSV del cliente con cada solicitud
- `timestamp_inyector.log` — Timestamp de cuándo se inyectó la falla

## Analizar resultados

```bash
python analizar.py
```

## Ejecución manual (terminal por terminal)

```bash
# Terminal 1: Réplicas
python replica.py A 5001
python replica.py B 5002
python replica.py C 5003

# Terminal 2: Dispatcher
python dispatcher.py

# Terminal 3: Dashboard (opcional)
python dashboard.py

# Terminal 4: Cliente
python client.py resultados/E1.csv

# Terminal 5: Inyector (a los 15 segundos)
python inyector.py B
```

## Configuración

Editar `config.json` para cambiar parámetros:

| Parámetro | Descripción | Valor por defecto |
|---|---|---|
| `T` | Intervalo de sondeo (s) | 1 |
| `t` | Timeout por sondeo (s) | 0.3 |
| `k` | Fallos consecutivos para CAÍDA | 2 |
| `num_replicas` | Cantidad de réplicas | 3 |
| `client_duration` | Duración del cliente (s) | 40 |
| `client_rate` | Solicitudes por segundo | 20 |

## Métricas esperadas

- **Tiempo de detección**: ~2s (T=1s × k=2)
- **% éxito durante caída**: 100% (redundancia activa protege al cliente)
- **% éxito total**: >99%

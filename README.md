# Taller Disponibilidad II — Ping/Echo + Redundancia Activa

## Requisitos
- Python 3.7 o superior
- No se necesitan dependencias externas (solo stdlib)

## Ejecución rápida

```bash
python run.py
```

Este comando:
1. Levanta 3 réplicas (puertos 5001, 5002, 5003)
2. Levanta el dispatcher (puerto 5000)
3. Ejecuta el cliente durante 40 segundos
4. Inyecta una falla en la réplica B a los 15 segundos
5. Genera los archivos de resultados

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

# Terminal 3: Cliente
python client.py resultados/E1.csv

# Terminal 4: Inyector (a los 15 segundos)
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

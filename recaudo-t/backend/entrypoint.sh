#!/bin/sh
# RECAUDO-T — entrypoint: elige rol según variables de entorno.
# Las réplicas se identifican por REPLICA_ID; el dispatcher por su ausencia.
set -e

if [ -n "$REPLICA_ID" ]; then
    echo "[entrypoint] iniciando réplica $REPLICA_ID"
    exec python backend/replica/main.py
fi

if [ -n "$CLIENT_DISPATCHER_URL" ]; then
    echo "[entrypoint] iniciando cliente de carga (web worker) contra $CLIENT_DISPATCHER_URL"
    exec python backend/client/worker.py
fi

echo "[entrypoint] iniciando dispatcher"
exec python backend/dispatcher/main.py
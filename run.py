import json
import subprocess
import time
import sys
import os
import signal

CONFIG = json.loads(open("config.json").read())

REPLICA_IDS = CONFIG["replica_ids"]
BASE_PORT = CONFIG["base_port"]
DISPATCHER_PORT = CONFIG["dispatcher_port"]
CLIENT_DURATION = CONFIG["client_duration"]
FAILURE_INJECT_AT = CONFIG["failure_inject_at_second"]
NUM_REPLICAS = CONFIG["num_replicas"]

processes = []


def cleanup(signum=None, frame=None):
    print("\nDeteniendo todos los procesos...")
    for p in processes:
        try:
            p.terminate()
        except Exception:
            pass
    for p in processes:
        try:
            p.wait(timeout=2)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    for f in ["bitacora_monitor.log", "timestamp_inyector.log"]:
        if os.path.exists(f):
            os.remove(f)

    os.makedirs("resultados", exist_ok=True)

    print("=" * 60)
    print("TALLER DISPONIBILIDAD II — Ping/Echo + Redundancia Activa")
    print("=" * 60)
    print(f"Réplicas: {NUM_REPLICAS} ({', '.join(REPLICA_IDS[:NUM_REPLICAS])})")
    print(f"Puertos réplicas: {BASE_PORT}-{BASE_PORT + NUM_REPLICAS - 1}")
    print(f"Puerto dispatcher: {DISPATCHER_PORT}")
    print(f"Parámetros: T={CONFIG['T']}s, t={CONFIG['t']}s, k={CONFIG['k']}")
    print(f"Duración cliente: {CLIENT_DURATION}s")
    print()

    print("[1/3] Iniciando réplicas...")
    for i in range(NUM_REPLICAS):
        rid = REPLICA_IDS[i]
        port = BASE_PORT + i
        p = subprocess.Popen(
            [sys.executable, "replica.py", rid, str(port)],
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        processes.append(p)
        print(f"  Réplica {rid} -> puerto {port} (PID {p.pid})")
        time.sleep(0.3)

    print("[2/4] Iniciando dispatcher...")
    dispatcher = subprocess.Popen(
        [sys.executable, "dispatcher.py"],
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    processes.append(dispatcher)
    print(f"  Dispatcher -> puerto {DISPATCHER_PORT} (PID {dispatcher.pid})")

    print("[3/4] Iniciando dashboard...")
    dashboard = subprocess.Popen(
        [sys.executable, "dashboard.py"],
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    processes.append(dashboard)
    print(f"  Dashboard -> http://127.0.0.1:8000 (PID {dashboard.pid})")

    print()
    time.sleep(2)

    print("[4/4] Iniciando cliente...")
    client = subprocess.Popen(
        [sys.executable, "client.py", "resultados/E1.csv"],
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    processes.append(client)
    print(f"  Cliente PID {client.pid}")

    print()
    print(f"Esperando {FAILURE_INJECT_AT}s antes de inyectar falla...")
    time.sleep(FAILURE_INJECT_AT)

    target_idx = 1
    target_id = REPLICA_IDS[target_idx]
    print(f"\n>>> INYECTANDO FALLA EN RÉPLICA {target_id} <<<\n")
    inyector = subprocess.Popen(
        [sys.executable, "inyector.py", target_id],
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    inyector.wait()

    print(f"\nEsperando a que el cliente termine ({CLIENT_DURATION - FAILURE_INJECT_AT}s restantes)...\n")
    client.wait()

    print("\n" + "=" * 60)
    print("EXPERIMENTO COMPLETADO")
    print("=" * 60)
    print("Archivos generados:")
    print("  - bitacora_monitor.log    (bitácora del monitor)")
    print("  - resultados/E1.csv       (CSV del cliente)")
    print("  - timestamp_inyector.log  (timestamp de inyección)")
    print()
    print("Para ver los resultados en el dashboard web:")
    print("  python dashboard.py   ->  http://127.0.0.1:8000")
    print("  python analizar.py    ->  métricas en consola")
    print()

    cleanup()


if __name__ == "__main__":
    main()

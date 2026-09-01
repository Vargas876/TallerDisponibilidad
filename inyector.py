import sys
import time
import urllib.request
import urllib.error
import json

CONFIG = json.loads(open("config.json").read())

REPLICA_IDS = CONFIG["replica_ids"]
BASE_PORT = CONFIG["base_port"]


def main():
    if len(sys.argv) < 2:
        print(f"Uso: python inyector.py <ID>")
        print(f"IDs disponibles: {', '.join(REPLICA_IDS)}")
        sys.exit(1)

    replica_id = sys.argv[1].upper()

    if replica_id not in REPLICA_IDS:
        print(f"ID '{replica_id}' no válido. IDs: {', '.join(REPLICA_IDS)}")
        sys.exit(1)

    idx = REPLICA_IDS.index(replica_id)
    port = BASE_PORT + idx

    timestamp_antes = time.time()
    print(f"[{timestamp_antes:.3f}] Inyectando falla en réplica {replica_id} (puerto {port})...")

    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/chaos/crash",
            method="POST"
        )
        urllib.request.urlopen(req, timeout=2)
    except Exception:
        pass

    timestamp_despues = time.time()
    print(f"[{timestamp_despues:.3f}] Réplica {replica_id} eliminada.")
    print(f"Timestamp de inyección: {timestamp_antes:.6f}")

    with open("timestamp_inyector.log", "a") as f:
        f.write(f"{timestamp_antes:.6f} {replica_id}\n")


if __name__ == "__main__":
    main()

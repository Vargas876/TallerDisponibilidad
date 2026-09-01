import time
import os
import csv

def main():
    bitacora_file = "bitacora_monitor.log"
    inyector_file = "timestamp_inyector.log"
    csv_file = "resultados/E1.csv"

    print("=" * 60)
    print("ANÁLISIS DE RESULTADOS")
    print("=" * 60)

    inyector_ts = None
    replica_caida = None

    if os.path.exists(inyector_file):
        with open(inyector_file, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    inyector_ts = float(parts[0])
                    replica_caida = parts[1]
        print(f"\nTimestamp de inyección: {inyector_ts:.6f}")
        print(f"Réplica target: {replica_caida}")
    else:
        print("No se encontró timestamp_inyector.log")
        return

    deteccion_ts = None
    if os.path.exists(bitacora_file):
        print(f"\nBitácora del monitor:")
        with open(bitacora_file, "r") as f:
            for line in f:
                print(f"  {line.strip()}")
                if "CAIDA" in line and replica_caida in line:
                    ts_str = line.split("]")[0].replace("[", "")
                    deteccion_ts = float(ts_str)
    else:
        print("No se encontró bitacora_monitor.log")
        return

    if inyector_ts and deteccion_ts:
        tiempo_deteccion = deteccion_ts - inyector_ts
        print(f"\nTiempo de detección: {tiempo_deteccion:.3f}s")
    else:
        print("\nNo se pudo calcular tiempo de detección")

    total = 0
    exitosos = 0
    replicas_usadas = set()

    if os.path.exists(csv_file):
        with open(csv_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                total += 1
                if int(row["exito"]) == 1:
                    exitosos += 1
                replicas_usadas.add(row["replica"])

        porcentaje = (exitosos / total * 100) if total > 0 else 0
        print(f"\nResultados del cliente:")
        print(f"  Total solicitudes: {total}")
        print(f"  Exitosas: {exitosos}")
        print(f"  Fallidas: {total - exitosos}")
        print(f"  % Éxito: {porcentaje:.1f}%")
        print(f"  Réplicas usadas: {', '.join(sorted(replicas_usadas))}")
    else:
        print("No se encontró resultados/E1.csv")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

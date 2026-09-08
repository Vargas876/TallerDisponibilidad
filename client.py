import json
import time
import csv
import sys
import os
import urllib.request
import urllib.error

CONFIG = json.loads(open("config.json").read())

DURACION = CONFIG["client_duration"]
TASA = CONFIG["client_rate"]
DISPATCHER_URL = f"http://127.0.0.1:{CONFIG['dispatcher_port']}"


def main():
    output_file = "resultados/E1.csv"
    if len(sys.argv) > 1:
        output_file = sys.argv[1]

    duracion = DURACION
    if len(sys.argv) > 2:
        duracion = float(sys.argv[2])

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    print(f"Cliente iniciado. Duración: {duracion}s, Tasa: {TASA} req/s")
    print(f"Salida: {output_file}")
    sys.stdout.flush()

    with open(output_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["timestamp_envio", "timestamp_respuesta", "exito", "replica"])

        start_time = time.time()
        total = 0
        exitosos = 0
        intervalo = 1.0 / TASA

        while True:
            elapsed = time.time() - start_time
            if elapsed >= duracion:
                break

            timestamp_envio = time.time()
            exito = 0
            replica_id = ""

            try:
                req = urllib.request.Request(f"{DISPATCHER_URL}/saldo/1234")
                resp = urllib.request.urlopen(req, timeout=1.0)
                data = json.loads(resp.read())
                exito = 1
                replica_id = data.get("replica_id", "")
            except Exception as e:
                exito = 0
                replica_id = ""

            timestamp_respuesta = time.time()
            total += 1
            exitosos += exito

            writer.writerow([
                f"{timestamp_envio:.6f}",
                f"{timestamp_respuesta:.6f}",
                exito,
                replica_id
            ])

            next_time = start_time + (total * intervalo)
            sleep_time = next_time - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)

    porcentaje = (exitosos / total * 100) if total > 0 else 0
    print(f"\nCliente terminó. Total: {total}, Exitosos: {exitosos} ({porcentaje:.1f}%)")


if __name__ == "__main__":
    main()

import subprocess
import sys
import time
import os
import signal

PYTHON = sys.executable
WD = os.path.dirname(os.path.abspath(__file__))

processes = []


def start(args):
    p = subprocess.Popen(
        [PYTHON] + args,
        cwd=WD,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    processes.append(p)
    return p


def kill_all():
    for p in processes:
        try:
            p.kill()
        except Exception:
            pass


try:
    print("[1/3] Iniciando réplicas A, B, C...")
    start(["replica.py", "A", "5001"])
    start(["replica.py", "B", "5002"])
    start(["replica.py", "C", "5003"])

    print("[2/3] Iniciando dispatcher...")
    start(["dispatcher.py"])
    time.sleep(2)

    import urllib.request
    import json

    print("[+] Verificando GET /estado...")
    resp = urllib.request.urlopen("http://127.0.0.1:5000/estado", timeout=3)
    print("  Estado:", resp.read().decode())

    print("[+] Verificando GET /saldo/1234...")
    resp = urllib.request.urlopen("http://127.0.0.1:5000/saldo/1234", timeout=3)
    print("  Saldo:", resp.read().decode())

    print("[+] Verificando GET /ping en réplica B...")
    resp = urllib.request.urlopen("http://127.0.0.1:5002/ping", timeout=3)
    print("  Ping B:", resp.read().decode())

    print("\n[3/3] Ejecutando experimento de 12s con falla a los 6s...")

    client = start(["client.py", "resultados/test.csv"])
    time.sleep(6)

    print("[>>>] Inyectando falla en réplica B...")
    start(["inyector.py", "B"])
    time.sleep(1)

    resp = urllib.request.urlopen("http://127.0.0.1:5000/estado", timeout=3)
    print("  Estado tras falla:", resp.read().decode())

    client.wait(timeout=60)
    print("\nCliente terminó.")

    print("\n--- BITÁCORA DEL MONITOR ---")
    if os.path.exists("bitacora_monitor.log"):
        print(open("bitacora_monitor.log").read())

finally:
    kill_all()

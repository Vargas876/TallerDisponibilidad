"""Orquestador de experimentos E0/E1 de RECAUDO-T.

Levanta rÃ©plicas + dispatcher, ejecuta el cliente de carga y (en E1) inyecta
una falla en FAILURE_INJECT_AT segundos contra TARGET_REPLICA. Al final
computa mÃ©tricas y edita results/metrics.json.

Modos:
  local   rÃ©plicas+dispatcher como procesos locales (python de este entorno)
  docker  rÃ©plicas+dispatcher en contenedores (docker compose), cliente/
          inyector/mÃ©tricas vÃ­a `docker compose run` de servicios "tools"

Uso (local):
  python scripts/run_experiment.py e0
  python scripts/run_experiment.py e1
  python scripts/run_experiment.py e1 --python C:\\ruta\\a\\python.exe

Uso (docker):
  docker compose up -d --build frontend dispatcher replica-a replica-b replica-c
  python scripts/run_experiment.py e1 --mode docker
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / "config" / ".env")

REPLICA_IDS = ["A", "B", "C", "D", "E", "F"]
NUM_REPLICAS = int(os.getenv("NUM_REPLICAS", "3"))
BASE_PORT = int(os.getenv("REPLICA_BASE_PORT", "8001"))
DISPATCHER_URL = os.getenv("DISPATCHER_URL", "http://127.0.0.1:8000")


def env_with(extra: dict[str, str]) -> dict[str, str]:
    env = os.environ.copy()
    env.update(extra)
    return env


class LocalRunner:
    def __init__(self, python: str, variant: str):
        self.python = python
        self.variant = variant
        self.procs: list[subprocess.Popen] = []
        self.suffix = variant[-1]

    def _spawn(self, args: list[str], env: dict | None = None) -> subprocess.Popen:
        p = subprocess.Popen(
            [self.python] + args,
            cwd=ROOT,
            env=env or os.environ.copy(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.procs.append(p)
        return p

    def _wait_dispatcher(self) -> bool:
        import httpx

        for _ in range(40):
            try:
                r = httpx.get(f"{DISPATCHER_URL}/estado", timeout=1.0)
                if r.status_code == 200 and r.json()["replicas_viva"] == NUM_REPLICAS:
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        return False

    def run(self) -> int:
        print(f"[runner] E{self.suffix} â€” levantando {NUM_REPLICAS} rÃ©plicas + dispatcher")
        for i in range(NUM_REPLICAS):
            rid = REPLICA_IDS[i]
            self._spawn(
                ["backend/replica/main.py"],
                env_with({"REPLICA_ID": rid, "REPLICA_PORT": str(BASE_PORT + i)}),
            )
            time.sleep(0.4)
        self._spawn(["backend/dispatcher/main.py"])
        if not self._wait_dispatcher():
            print("[runner] ERROR: dispatcher no quedÃ³ listo")
            self.shutdown()
            return 1

        out_csv = ROOT / "results" / f"e{self.suffix}.csv"
        dur = int(os.getenv("EXPERIMENT_DURATION", "40"))
        rate = int(os.getenv("CLIENT_RATE", "20"))
        print(f"[runner] cliente {rate} req/s x {dur}s -> {out_csv.name}")
        client = self._spawn(
            [
                "backend/client/client.py",
                "--out", str(out_csv),
                "--duration", str(dur),
                "--rate", str(rate),
            ]
)
        time.sleep(2.0)

        if self.suffix == "1":
            target = os.getenv("TARGET_REPLICA", "B").upper()
            at = int(os.getenv("FAILURE_INJECT_AT", "15"))
            print(f"[runner] falla contra rÃ©plica {target} en t+{at}s")
            time.sleep(max(0, at - 2.0))
            inj_path = ROOT / "results" / "injection_e1.log"
            inj = self._spawn(
                [
                    "backend/injector/injector.py",
                    target,
                    "--log", str(inj_path),
                    "--dispatcher", DISPATCHER_URL,
                ]
            )
            inj.wait(timeout=15)
            if inj.returncode != 0:
                print(f"[runner] ADVERTENCIA: inyector rc={inj.returncode} (no hubo inyecciÃ³n)")
            else:
                rdelay = int(os.getenv("RECOVERY_DELAY", "5"))
                time.sleep(rdelay)
                idx = REPLICA_IDS.index(target)
                self._spawn(
                    ["backend/replica/main.py"],
                    env_with({"REPLICA_ID": target, "REPLICA_PORT": str(BASE_PORT + idx)}),
                )
                print(f"[runner] rÃ©plica {target} reiniciada (evidencia de recuperaciÃ³n)")

        client.wait(timeout=dur + 30)
        print("[runner] cliente finalizado")
        self.shutdown()

        inj = ROOT / "results" / "injection_e1.log"
        metrics = self._spawn(
            [
                "backend/metrics.py",
                "--experiment", f"e{self.suffix}",
                "--csv", str(out_csv),
                "--injection", str(inj),
            ]
        )
        metrics.wait(timeout=20)
        return metrics.returncode if metrics.returncode == 0 else 1

    def shutdown(self) -> None:
        for p in self.procs:
            try:
                p.terminate()
            except Exception:
                pass
        for p in self.procs:
            try:
                p.wait(timeout=3)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass


class DockerRunner:
    def __init__(self, variant: str):
        self.suffix = variant[-1]

    def _dc(self, *args: str, check: bool = True) -> str:
        res = subprocess.run(
["docker", "compose", *args], cwd=ROOT, capture_output=True, text=True
        )
        if check and res.returncode != 0:
            raise SystemExit("docker compose fallÃ³: " + res.stdout + res.stderr)
        return res.stdout + res.stderr

    def run(self) -> int:
        dur = int(os.getenv("EXPERIMENT_DURATION", "40"))
        rate = int(os.getenv("CLIENT_RATE", "20"))
        print("[runner] docker â€” asegurando servicios")
        self._dc("up", "-d", "--build", "replica-a", "replica-b", "replica-c", "dispatcher", "frontend")
        time.sleep(6)

        out = f"/app/results/e{self.suffix}.csv"
        name = f"recaudo-e{self.suffix}-client"
        print(f"[runner] docker â€” cliente {rate} req/s Ã— {dur}s")
        self._dc("rm", "-f", name, check=False)
        self._dc(
            "run", "--rm", "-d", "--no-deps", "--name", name, "client",
            "--out", out, "--duration", str(dur), "--rate", str(rate),
        )

        if self.suffix == "e1":
            target = os.getenv("TARGET_REPLICA", "B").upper()
            at = int(os.getenv("FAILURE_INJECT_AT", "15"))
            print(f"[runner] docker â€” falla contra {target} en t+{at}s")
            time.sleep(max(0, at - 2.0))
            self._dc(
                "run", "--rm", "--no-deps", "injector", target,
                "--log", "/app/results/injection_e1.log", "--dispatcher",
                "http://dispatcher:8000",
            )

        # esperar a que termine el contenedor del cliente
        for _ in range(dur + 30):
            res = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Status}}", name],
                cwd=ROOT, capture_output=True, text=True,
            )
            if res.returncode != 0:
                break
            time.sleep(1)

        self._dc(
            "run", "--rm", "--no-deps", "metrics", "--experiment", f"e{self.suffix}",
            "--csv", out, "--injection", "/app/results/injection_e1.log",
        )
        return 0


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="RECAUDO-T orquestador E0/E1")
    ap.add_argument("variant", choices=["e0", "e1"])
    ap.add_argument("--mode", choices=["local", "docker"], default="local")
    ap.add_argument("--python", default=sys.executable)
    args = ap.parse_args()

    # bitÃ¡coras frescas por corrida: evita que mÃ©tricas contamine con eventos viejos
    for rel in ("logs/monitor.log", "results/injection_e1.log"):
        p = ROOT / rel
        p.parent.mkdir(exist_ok=True)
        p.write_text("", encoding="utf-8")

    runner = DockerRunner(args.variant) if args.mode == "docker" else LocalRunner(args.python, args.variant)
    start = time.time()
    rc = runner.run()
    print(f"[runner] E{args.variant[-1]} finalizado en {time.time() - start:.1f}s (rc={rc})")
    return rc


if __name__ == "__main__":
    sys.exit(main())

# =========================================================
# RECAUDO-T — Availability & Resilience Monitor
# Makefile (opcional; equivalentes directos en comandos python/npm)
# =========================================================

PY      ?= .venv/Scripts/python.exe
COMPOSE ?= docker compose
NPM     ?= npm

RUNTIME = dispatcher replica-a replica-b replica-c frontend

.PHONY: help setup up down logs build frontend-build \
        dev live smoke e0 e1 q3 e0-docker e1-docker clean

help: ## listar objetivos
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

setup: ## preparar entorno local (venv + frontend)
	python -m venv .venv
	$(PY) -m pip install -r requirements.txt
	cd frontend && $(NPM) install

up: ## levantar pila con Docker (dispatcher + réplicas + frontend)
	$(COMPOSE) up -d --build $(RUNTIME)

down: ## detener pila Docker
	$(COMPOSE) down

logs: ## logs de la pila Docker
	$(COMPOSE) logs -f --tail=50

build: frontend-build ## build del frontend

frontend-build:
	cd frontend && $(NPM) run build

dev: ## desarrollo local: réplicas+dispatcher y Next dev
	$(PY) scripts/dev_local.py

live: ## smoke test punta a punta (pila local + Frontend + WebSocket)
	$(PY) scripts/smoke_live.py

smoke: live ## alias

e0: ## experimento E0 local (sin fallas)
	$(PY) scripts/run_experiment.py e0

e1: ## experimento E1 local (inyección de falla + recuperación)
	$(PY) scripts/run_experiment.py e1

q3: ## escenario Q3: saldo roto con ping OK (limitación del Ping/Echo)
	$(PY) scripts/scenario_q3.py

e0-docker: ## experimento E0 sobre Docker
	$(PY) scripts/run_experiment.py e0 --mode docker

e1-docker: ## experimento E1 sobre Docker
	$(PY) scripts/run_experiment.py e1 --mode docker

clean: ## limpiar artefactos de ejecución
	rm -f logs/*.log logs/*.log.err results/*.csv results/*.json
	cd frontend && rm -rf .next dev_db|true
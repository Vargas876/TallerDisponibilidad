# RECAUDO-T — imagen del backend (dependencyas + código)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ backend/

RUN chmod +x backend/entrypoint.sh

EXPOSE 8000 8001

# El entrypoint elige el rol según REPLICA_ID (dispatcher por defecto)
CMD ["sh", "/app/backend/entrypoint.sh"]
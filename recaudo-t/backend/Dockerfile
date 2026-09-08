# RECAUDO-T — imagen del backend (dependencyas + código)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ backend/

EXPOSE 8000

# Comandos de servicio se definen en docker-compose.yml
CMD ["python", "backend/dispatcher/main.py"]
# Стадия 1: Сборка зависимостей
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gcc python3-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

# Создаем необходимые директории
RUN mkdir -p /app/.crewai_storage /app/docs

# Стадия 2: Финальный образ
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser && \
    mkdir -p /app && chown -R appuser:appuser /app

WORKDIR /app

# Копируем установленные пакеты из стадии builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Копируем код приложения
COPY --chown=appuser:appuser . .

# Создаем необходимые директории
RUN mkdir -p /home/appuser/.local/share/app && \
    mkdir -p /app/.crewai_storage /app/docs && \
    chown -R appuser:appuser /home/appuser /app/.crewai_storage /app/docs

# Переключаемся на непривилегированного пользователя
USER appuser

# Переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    CREWAI_STORAGE_DIR=/app/.crewai_storage

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

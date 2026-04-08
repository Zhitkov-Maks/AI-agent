FROM python:3.12-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Создаем непривилегированного пользователя
RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

WORKDIR /app

# Копируем и устанавливаем зависимости от root (системная установка)
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY --chown=appuser:appuser . .

# Создаем необходимые директории
RUN mkdir -p /home/appuser/.local/share/app && \
    chown -R appuser:appuser /home/appuser

# Переключаемся на непривилегированного пользователя
USER appuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Указываем альтернативный путь для хранения данных CrewAI
ENV CREWAI_STORAGE_DIR=/app/.crewai_storage

# Создаем директорию для CrewAI в папке приложения
RUN mkdir -p /app/.crewai_storage

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
import os
from celery import Celery
from mylogger import logger

# Настройки подключения к Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_DB = os.getenv("REDIS_DB", "0")

# URL для брокера и хранилища результатов
# Используем разные базы данных для брокера и результатов
BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"      # База 0 для брокера
RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/1"  # База 1 для результатов

# Создание экземпляра Celery
celery_app = Celery(
    "documentation_generator",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=["tasks"]  # Автоматическое обнаружение задач
)

# Конфигурация Celery
celery_app.conf.update(
    # Сериализация
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Таймауты
    task_time_limit=30 * 60,       # 30 минут максимум
    task_soft_time_limit=25 * 60,  # 25 минут до мягкого таймаута

    # Отслеживание
    task_track_started=True,
    task_send_sent_event=True,

    # Временная зона
    timezone="Europe/Moscow",
    enable_utc=True,

    # Максимальное количество задач на воркер
    worker_prefetch_multiplier=1,

    # Настройки результата
    result_expires=3600,  # Результаты живут 1 час
    result_backend_transport_options={
        "retry_policy": {
            "timeout": 5.0,
            "max_retries": 3,
        }
    },
    broker_connection_retry_on_startup=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Настройки для Redis (опционально)
celery_app.conf.broker_transport_options = {
    "visibility_timeout": 3600,  # 1 час видимости задачи
    "fanout_prefix": True,
    "fanout_patterns": True,
}

logger.info(f"Celery приложение инициализировано с брокером: {BROKER_URL}")

# Алиас для совместимости с командой celery -A celery_app.celery
celery = celery_app

import asyncio
from typing import Dict, Any

from celery import Task
from celery.result import AsyncResult

from mylogger import logger
from celery_app import celery_app
from agents import generate_and_validate_documentation
from storage import save_document
from rag import add_document, search_documentation


class DocumentGenerationTask(Task):
    """Базовый класс для задачи генерации документации с обработкой ошибок."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Обработка ошибок задачи"""
        logger.error(
            f"Задача {task_id} завершилась с ошибкой: {exc}",
            exc_info=einfo
        )

    def on_success(self, retval, task_id, args, kwargs):
        """Обработка успешного выполнения"""
        logger.info(
            f"Задача {task_id} успешно выполнена. "
            f"Результат: {retval.get('file_path', 'N/A')}"
        )


@celery_app.task(
    bind=True,
    base=DocumentGenerationTask,
    name="generate_documentation",
    max_retries=3,
    default_retry_delay=60,  # 60 секунд между повторными попытками
    autoretry_for=(Exception,),  # Автоматический повтор при любых исключениях
    retry_backoff=True,  # Экспоненциальная задержка
    retry_backoff_max=600  # Максимум 10 минут
)
def generate_documentation_task(self, query: str) -> Dict[str, Any]:
    """
    Celery задача для генерации документации

    Args:
        query: Поисковый запрос для генерации документации

    Returns:
        Dict с результатами генерации
    """
    try:
        logger.info(f"Начало генерации документации для запроса: {query!r}")

        # 1. Проверяем, не существует ли уже документ
        existing = search_documentation(query, similarity_threshold=0.75)
        if existing:
            logger.info(f"Документ для {query!r} уже существует")
            return {
                "status": "skipped",
                "message": "Документ уже существует",
                "query": query
            }

        # 2. Генерация документации (блокирующая операция)
        # Запускаем в отдельном потоке, чтобы не блокировать event loop
        content = generate_and_validate_documentation(query)

        # 3. Валидация формата
        if not content or not content.strip().startswith('###'):
            logger.error(f"Неверный формат документа для запроса: {query}")
            raise ValueError("Неверный формат документа для запроса")

        # 4. Сохранение файла
        file_path = save_document(content, query)
        logger.info(f"Документ сохранен: {file_path}")

        # 5. Добавление в RAG
        added = add_document(content, file_path)

        if not added:
            logger.warning(f"Не удалось добавить документ в RAG: {file_path}")

        # Возвращаем результат
        return {
            "status": "success",
            "message": "Документ успешно создан",
            "query": query,
            "file_path": file_path,
            "content": content,
            "rag_added": added
        }

    except Exception as e:
        logger.error(f"Ошибка в задаче генерации: {e}", exc_info=True)

        # Повторный вызов задачи с экспоненциальной задержкой
        raise self.retry(exc=e)


@celery_app.task(name="check_task_status")
def check_task_status(task_id: str) -> Dict[str, Any]:
    """
    Проверка статуса задачи

    Args:
        task_id: ID задачи Celery

    Returns:
        Информация о статусе задачи
    """
    task = AsyncResult(task_id, app=celery_app)

    result = {
        "task_id": task_id,
        "status": task.state,
    }

    if task.state == "SUCCESS":
        result["result"] = task.result
    elif task.state == "FAILURE":
        result["error"] = str(task.info)
    elif task.state == "PENDING":
        result["message"] = "Задача ожидает выполнения"
    elif task.state == "STARTED":
        result["message"] = "Задача выполняется"

    return result


@celery_app.task(name="cleanup_old_results")
def cleanup_old_results():
    """Очистка старых результатов (для периодического выполнения)."""
    # Логика очистки старых результатов
    logger.info("Очистка старых результатов задач выполнена")
    return {
        "status": "cleaned", "timestamp": str(asyncio.get_event_loop().time())
    }

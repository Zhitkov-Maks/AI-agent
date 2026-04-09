import asyncio

from celery.result import AsyncResult
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.logger import logger
from app.health import check_all_services

from app.rag import initialize_rag_from_docs, search_documentation
from app.schemas import (
    SearchRequest,
    SearchResponse,
    GenerateRequest,
    GenerateResponse
)
from app.celery_app import celery_app
from app.tasks import generate_documentation_task, check_task_status


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Инициализация RAG из docs/")

    # Выполняем загрузку эмбеддингов в отдельном потоке
    await asyncio.to_thread(initialize_rag_from_docs)

    logger.info("Сервис готов к работе")
    yield


app = FastAPI(title="AI Docs Assistant", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы (GET, POST, DELETE и т.д.)
    allow_headers=["*"],  # Разрешить все заголовки
)


@app.post('/search', response_model=SearchResponse)
async def search_docs(request: SearchRequest):
    """
    Выполняет семантический поиск в базе документации.
    """
    result = search_documentation(request.query)

    if result:
        return SearchResponse(found=True, content=result)
    else:
        return SearchResponse(
            found=False,
            message='Документация не найдена. '
                    'Используйте /generate для создания новой.'
        )


@app.post('/generate', response_model=GenerateResponse)
async def generate_docs(
    request: GenerateRequest, background_tasks: BackgroundTasks
):
    """
    Генерирует документацию асинхронно - ответ приходит сразу,
    а генерация идет в фоне.
    """
    # Быстрая проверка существования
    existing = search_documentation(request.query, similarity_threshold=0.75)

    if existing:
        return GenerateResponse(
            success=False,
            message='Документ уже существует. Используйте /search.'
        )

    task = generate_documentation_task.delay(request.query)

    return GenerateResponse(
        success=True,
        message=f'Задача на генерацию запущена. Task ID: {task.id}',
        content=None,
        file_path=None,
        task_id=task.id
    )


@app.get('/task/{task_id}')
async def get_task_status(task_id: str):
    """
    Получение статуса задачи по ID
    """
    return await asyncio.to_thread(check_task_status, task_id)


@app.delete('/task/{task_id}')
async def abort_task(task_id: str):
    """
    Отмена выполнения задачи
    """
    task = AsyncResult(task_id, app=celery_app)

    if task.state in ["PENDING", "STARTED"]:
        task.revoke(terminate=True)
        return {"status": "aborted", "task_id": task_id}

    return {
        "status": "task_not_running",
        "task_id": task_id,
        "current_state": task.state
    }


@app.get('/health')
async def health_check():
    """
    Расширенный health-check:
    - зависимости (Qdrant, Ollama),
    - данные (docs/),
    - функциональность (canary RAG-запрос).
    """
    return await check_all_services()

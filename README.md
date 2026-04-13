```markdown
# AI Docs Assistant 🤖

Интеллектуальная система для автоматической генерации и семантического поиска API-документации с использованием RAG (Retrieval-Augmented Generation), LLM и векторных баз данных.

## 📋 Оглавление

- [Архитектура](#архитектура)
- [Технологический стек](#технологический-стек)
- [Требования](#требования)
- [Установка и запуск](#установка-и-запуск)
- [Конфигурация](#конфигурация)
- [API Endpoints](#api-endpoints)
- [Использование](#использование)
- [Мониторинг](#мониторинг)
- [Разработка](#разработка)
- [Безопасность](#безопасность)

## 🏗 Архитектура
╭──────────────╮ ╭──────────────╮ ╭──────────────╮
│ Vue.js       │────▶ FastAPI   │────▶  Redis    │
│ Frontend     │ │    Backend   │ │     Broker   │
╰──────────────╯ ╰──────────────╯ ╰──────────────╯
│                       │                │        |
│                       ▼                ▼        |
│               ╭──────────────╮  ╭──────────────╮|
│               │ Qdrant       │◀─│ Celery       │|
│               │ Vector DB    │  │ Worker       │|
│               ╰──────────────╯  ╰──────────────╯|
│                                       │         |
│                                       ▼         |
│                                ╭──────────────╮ |
│                                │     Ollama   │ |
│                                |      LLM     │ |
│                                ╰──────────────╯ |
│                                                 │
╰─────────────────────────────────────────────────╯
HTTP/REST API

### Компоненты системы:

- **FastAPI Backend** - REST API сервис для поиска и генерации документации
- **Celery Worker** - Асинхронная обработка задач генерации документации
- **Qdrant** - Векторная база данных для семантического поиска
- **Redis** - Брокер сообщений и бэкенд для Celery
- **Ollama** - Локальный LLM (модель для генерации)
- **Vue.js Frontend** - Веб-интерфейс пользователя
- **Flower** - Мониторинг Celery задач

## 🛠 Технологический стек

| Компонент | Технология | Версия |
|-----------|------------|--------|
| Backend | FastAPI | 0.104+ |
| Task Queue | Celery | 5.3+ |
| Vector DB | Qdrant | latest |
| Message Broker | Redis | 7-alpine |
| LLM | Ollama | latest |
| Embedding Model | mxbai-embed-large | latest |
| Frontend | Vue.js 3 | latest |
| Monitoring | Flower | latest |
| Containerization | Docker | 20.10+ |

## 📦 Требования

- Docker Engine 20.10+
- Docker Compose V2
- 8GB RAM (минимально)
- 4 CPU cores (рекомендуется)
- 10GB свободного дискового пространства

## 🚀 Установка и запуск

### 1. Клонирование репозитория

```bash
git clone https://github.com/your-org/ai-docs-assistant.git
cd ai-docs-assistant
```

### 2. Настройка окружения

Создайте файл `.env` в корне проекта:

```bash
# .env файл
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=api_docs
QDRANT_API_KEY=$(openssl rand -base64 32)

EMBEDDING_MODEL_NAME=mxbai-embed-large
VECTOR_SIZE=1024

SECRET_KEY=$(openssl rand -base64 32)
API_KEY=ollama

OLLAMA_HOST=host.docker.internal
OLLAMA_PORT=11434
OLLAMA_MODEL=ollama/my-api-docs

REDIS_PASSWORD=$(openssl rand -base64 32)

FLOWER_USER=admin5
FLOWER_PASSWORD=ikfcfifgjijcctbcjcfkfceire

ENVIRONMENT=production
```

### 3. Запуск Ollama (локально)

```bash
# Установите Ollama с официального сайта
curl -fsSL https://ollama.com/install.sh | sh

# Загрузите необходимые модели
ollama pull mxbai-embed-large  # Для эмбеддингов
ollama pull my-api-docs        # Ваша кастомная модель для генерации

# Запустите сервер Ollama
ollama serve
```

### 4. Сборка и запуск всех сервисов

```bash
docker-compose up -d
```

### 5. Проверка статуса

```bash
docker-compose ps
curl http://localhost:8000/health
```

### 6. Доступ к сервисам

| Сервис | URL | Назначение |
|--------|-----|------------|
| Frontend | http://localhost | Веб-интерфейс |
| Backend API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Swagger документация |
| Flower | http://localhost:5555 | Мониторинг задач |
| Qdrant | http://localhost:6333 | Dashboard векторной БД |

## ⚙️ Конфигурация

### Основные настройки (settings.py)

```python
# LLM настройки
OLLAMA_MODEL = "ollama/my-api-docs"  # Кастомная модель для генерации
EMBEDDING_MODEL_NAME = "mxbai-embed-large"  # Модель для эмбеддингов

# Векторная база данных
QDRANT_HOST = "qdrant"
QDRANT_PORT = 6333
QDRANT_COLLECTION_NAME = "api_docs"
VECTOR_SIZE = 1024  # Размерность эмбеддинга для mxbai-embed-large

# RAG параметры
CHUNK_SIZE = 1000  # Размер чанка документа
CHUNK_OVERLAP = 200  # Перекрытие чанков
```

### Переменные окружения

Все переменные окружения задаются в файле `.env`:

```bash
# Обязательные
REDIS_PASSWORD=...          # Автоматически генерируется
SECRET_KEY=...              # Автоматически генерируется
QDRANT_API_KEY=...          # Автоматически генерируется

# Модели
EMBEDDING_MODEL_NAME=mxbai-embed-large
OLLAMA_MODEL=ollama/my-api-docs

# Мониторинг
FLOWER_USER=admin5
FLOWER_PASSWORD=ikfcfifgjijcctbcjcfkfceire

# Окружение
ENVIRONMENT=production
```

## 📡 API Endpoints

### Поиск документации

```http
POST /search
Content-Type: application/json

{
    "query": "Как авторизоваться через JWT"
}
```

**Ответ:**
```json
{
    "found": true,
    "content": "### POST /api/auth/login\n**Описание**: ..."
}
```

### Генерация документации

```http
POST /generate
Content-Type: application/json

{
    "query": "POST /api/users метод создания пользователя"
}
```

**Ответ:**
```json
{
    "success": true,
    "message": "Задача на генерацию запущена. Task ID: abc-123",
    "task_id": "abc-123"
}
```

### Получение статуса задачи

```http
GET /task/{task_id}
```

**Ответ:**
```json
{
    "task_id": "abc-123",
    "status": "SUCCESS",
    "result": {
        "file_path": "docs/20231215_143022_post_api_users.md",
        "rag_added": true
    }
}
```

### Отмена задачи

```http
DELETE /task/{task_id}
```

### Health Check

```http
GET /health
```

## 💻 Использование

### Через веб-интерфейс

1. Откройте http://localhost
2. Введите поисковый запрос в поле ввода
3. Если документация не найдена, система предложит её сгенерировать
4. Отслеживайте статус генерации в интерфейсе

### Через API (curl)

```bash
# Поиск документации
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"GET /api/users endpoint"}'

# Генерация документации
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"query":"POST /api/products endpoint"}'

# Проверка статуса
curl http://localhost:8000/task/abc-123
```

### Управление документацией

Документация хранится в директории `./docs/` в формате Markdown:

```markdown
### POST /api/users
**Описание**: Создание нового пользователя
**Параметры**:
- name (string, required) - Имя пользователя
- email (string, required) - Email пользователя

**Ответ**:
```json
{
  "id": 1,
  "name": "John",
  "email": "john@example.com"
}
```
```

## 📊 Мониторинг

### Flower Dashboard

Доступен по адресу: http://localhost:5555

- **Задачи**: Просмотр всех задач (успешные, выполняющиеся, проваленные)
- **Воркеры**: Статистика по воркерам (загрузка CPU, память)
- **Графики**: Временные диаграммы выполнения задач

### Логи

```bash
# Просмотр логов всех сервисов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f app
docker-compose logs -f celery
```

### Метрики здоровья

```bash
# Проверка всех сервисов
curl http://localhost:8000/health

# Ответ включает проверку:
# - Qdrant подключения
# - Redis доступности  
# - Наличия docs/ директории
# - RAG функциональности
```

## 🔧 Разработка

### Локальный запуск (без Docker)

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск Redis
redis-server --requirepass your_password

# Запуск FastAPI
uvicorn main:app --reload --port 8000

# Запуск Celery worker (в отдельном терминале)
celery -A celery_app worker --loglevel=info
```

### Добавление новых моделей

1. Измените `OLLAMA_MODEL` в `.env`
2. Обновите `EMBEDDING_MODEL_NAME` и `VECTOR_SIZE` в `.env`
3. Пересоберите эмбеддинги: удалите коллекцию Qdrant и перезапустите приложение

### Расширение функциональности

- **Новые типы документов**: Добавьте обработчики в `rag.py`
- **Дополнительные агенты**: Расширьте `agents.py`
- **Кастомные воркеры**: Создайте новые задачи в `tasks.py`

## 🔒 Безопасность

### Рекомендации

1. **Используйте сильные пароли** - все пароли генерируются автоматически через `openssl rand -base64 32`
2. **Ограничьте сетевой доступ** через настройки Docker networks
3. **Регулярно обновляйте** зависимости и образы
4. **Настройте rate limiting** для API endpoints
5. **Храните `.env` файл в безопасности** и не коммитьте его в репозиторий

### Безопасность по умолчанию

- Все пароли генерируются случайным образом при создании `.env`
- Используются внутренние Docker сети для изоляции сервисов
- Qdrant защищен API ключом
- Redis защищен паролем
- Flower защищен базовой аутентификацией

### Переменные с автоматической генерацией

```bash
# Эти переменные генерируются автоматически и уникальны для каждой установки
QDRANT_API_KEY=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
```

## 📝 Примечания

- **Кастомная модель**: Система использует вашу модель `ollama/my-api-docs` для генерации документации
- **Embedding модель**: `mxbai-embed-large` обеспечивает качественные эмбеддинги размерности 1024
- **Production режим**: Приложение работает в production режиме с оптимизированными настройками
- **Мониторинг**: Доступ к Flower защищен логином `admin5` и указанным паролем
```


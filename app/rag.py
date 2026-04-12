from pathlib import Path
import asyncio
import os

from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from mylogger import logger
from settings import settings
from agents import generate_and_validate_documentation
from storage import save_document


QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)

# Конфигурация векторного хранилища
collection_name = settings.QDRANT_COLLECTION_NAME
embedding_model_name = settings.EMBEDDING_MODEL_NAME
vector_size = settings.VECTOR_SIZE

# Инициализация клиента Qdrant
client = QdrantClient(
    settings.QDRANT_HOST,
    port=settings.QDRANT_PORT,
    api_key=QDRANT_API_KEY if QDRANT_API_KEY else "",
    https=False
)

# Инициализация embedding-модели через Ollama
embeddings = OllamaEmbeddings(model=embedding_model_name)

# Векторное хранилище LangChain
vector_store = None

# Текст-сплиттер для чанков (улучшает поиск)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,  # Размер чанка в символах
    chunk_overlap=200,  # Перекрытие между чанками
    separators=["\n\n", "\n", " ", ""],
    length_function=len,
)


def init_vector_store():
    """Инициализирует векторное хранилище"""
    global vector_store
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
        distance=Distance.COSINE,
    )
    return vector_store


def ensure_collection_exists():
    """Проверяет существование коллекции и создает если нужно."""
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size, distance=Distance.COSINE
            ),
        )
        logger.info(f"✅ Коллекция {collection_name} создана")
        return False
    else:
        logger.info(f"📁 Коллекция {collection_name} уже существует")
        return True


def initialize_rag_from_docs() -> None:
    """
    Загружает все .md-файлы из директории docs/ с разбиением на чанки.
    """
    collection_exists = ensure_collection_exists()
    init_vector_store()

    docs_dir = Path("docs")
    if not docs_dir.exists():
        logger.warning("Директория docs/ не найдена")
        return

    # Проверяем наличие документов в коллекции
    if collection_exists:
        try:
            collection_info = client.get_collection(collection_name)
            points_count = collection_info.points_count if hasattr(
                collection_info, 'points_count'
            ) else 0
            if points_count > 0:
                logger.info(
                    f"Коллекция уже содержит {points_count} чанков, "
                    "пропускаем загрузку"
                )
                return
        except Exception as e:
            logger.warning(f"Не удалось проверить коллекцию: {e}")

    documents = []
    for file_path in docs_dir.glob("*.md"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": str(file_path),
                            "filename": file_path.name,
                            "title": file_path.stem
                        }
                    )
                    documents.append(doc)
                    logger.info(
                        f"📄 Загружен файл: {file_path.name} "
                        f"({len(content)} символов)"
                    )
        except Exception as exc:
            logger.error(f"Ошибка чтения файла {file_path}: {exc}")

    if documents:
        # Разбиваем документы на чанки для лучшего поиска
        chunks = text_splitter.split_documents(documents)
        logger.info(
            f"📦 Разбито на {len(chunks)} чанков "
            "(было {len(documents)} документов)"
        )

        vector_store.add_documents(chunks)
        logger.info(f"✅ Загружено {len(chunks)} чанков в RAG-хранилище")
    else:
        logger.warning("В директории docs/ не найдено .md-файлов")


def search_documentation(
    query: str,
    k: int = 3,
    similarity_threshold: float = 0.5
) -> list | None:
    """Выполняет семантический поиск по документации API."""
    global vector_store

    if vector_store is None:
        init_vector_store()

    try:
        logger.info(f'🔍 Семантический поиск: {query!r}')
        results = vector_store.similarity_search_with_score(
            query,
            k=k,
            score_threshold=similarity_threshold
        )

        if results:
            logger.info(f'📊 Найдено {len(results)} результатов:')
            for i, (doc, score) in enumerate(results, 1):
                logger.info(
                    f'  {i}. {doc.metadata.get("filename", "unknown")} '
                    f'(score={score:.3f}) - {doc.page_content[:100]}...'
                )

            return results[0][0].page_content

        logger.info(f'❌ Релевантные документы не найдены для {query!r}')
        return None

    except Exception as exc:
        logger.error(f'Ошибка при выполнении RAG-поиска: {exc}', exc_info=True)
        return None


def add_document(content: str, file_path: str) -> bool:
    """Добавляет документ в существующую коллекцию"""
    global vector_store

    if vector_store is None:
        init_vector_store()

    # Разбиваем новый документ на чанки
    doc = Document(
        page_content=content,
        metadata={
            "source": str(file_path),
            "filename": Path(file_path).name,
            "title": Path(file_path).stem
        }
    )

    chunks = text_splitter.split_documents([doc])

    try:
        vector_store.add_documents(chunks)
        logger.info(
            f"✅ Документ добавлен в RAG: {file_path} ({len(chunks)} чанков)"
        )
        return True
    except Exception as e:
        logger.error(f"Ошибка добавления документа в RAG: {e}")
        return False


async def generate_document_background(query: str):
    """Фоновая задача для генерации документа"""
    try:
        content = await asyncio.to_thread(
            generate_and_validate_documentation, query
        )

        if not content.strip().startswith('###'):
            logger.error(f'Неверный формат документа для запроса: {query}')
            return

        file_path = await asyncio.to_thread(save_document, content, query)
        added = await asyncio.to_thread(add_document, content, file_path)

        if added:
            logger.info(f"✅ Документ создан и добавлен в RAG: {file_path}")
        else:
            logger.warning(f"⚠️ Документ не был добавлен в RAG: {file_path}")

    except Exception as e:
        logger.error(f'❌ Ошибка фоновой генерации: {e}', exc_info=True)

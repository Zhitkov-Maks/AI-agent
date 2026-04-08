from pathlib import Path
import asyncio

from langchain_core.documents import Document
from flashrank import Ranker, RerankRequest
from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.logger import logger
from app.settings import settings
from app.agents import generate_and_validate_documentation
from app.storage import save_document

# Конфигурация векторного хранилища
collection_name = settings.QDRANT_COLLECTION_NAME
embedding_model_name = settings.EMBEDDING_MODEL_NAME
vector_size = settings.VECTOR_SIZE

# Инициализация клиента Qdrant и создание коллекции
client = QdrantClient(settings.QDRANT_HOST, port=settings.QDRANT_PORT)
ranker = Ranker()

if client.collection_exists(collection_name):
    client.delete_collection(collection_name)

client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
)

# Инициализация embedding-модели через Ollama
embeddings = OllamaEmbeddings(model=embedding_model_name)

# Векторное хранилище LangChain
vector_store = QdrantVectorStore(
    client=client,
    collection_name=collection_name,
    embedding=embeddings,
    distance=Distance.COSINE,
)


def initialize_rag_from_docs() -> None:
    """
    Загружает все .md-файлы из директории docs/
    в векторную базу при старте сервиса.
    """
    docs_dir = Path("docs")
    if not docs_dir.exists():
        logger.warning("Директория docs/ не найдена")
        return

    documents = []
    for file_path in docs_dir.glob("*.md"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    documents.append(
                        Document(
                            page_content=content,
                            metadata={"source": str(file_path)}
                        )
                    )
        except Exception as exc:
            logger.error(f"Ошибка чтения файла {file_path}: {exc}")

    if documents:
        vector_store.add_documents(documents)
        logger.info(f"Загружено {len(documents)} документов в RAG-хранилище")
    else:
        logger.warning("В директории docs/ не найдено .md-файлов")


def search_documentation(
    query: str,
    retrieval_k: int = 10,
    k: int = 3,
    similarity_threshold: float = 0.62
) -> str | None:
    """Выполняет семантический поиск по документации API."""
    try:
        logger.info(f"Семантический поиск: {query!r}")
        docs_with_scores = vector_store.similarity_search_with_score(
            query, k=retrieval_k, score_threshold=similarity_threshold
        )

        if not docs_with_scores:
            logger.info(f"Документы не найдены для {query!r}")
            return None

        # 2. Конвертируем в формат, понятный FlashRank
        passages = []
        for doc, _ in docs_with_scores:
            passages.append({
                "id": doc.metadata.get("source", str(id(doc))),
                "text": doc.page_content,
                "meta": {"source": doc.metadata.get("source", "unknown")}
            })

        reranked_results = ranker.rerank(
            RerankRequest(query=query, passages=passages)
        )

        if reranked_results:
            doc = reranked_results[0]
            logger.info(
                f"Найден релевантный документ ({doc['meta']['source']}) "
                f"(score={doc['score']:.3f}) для {query!r}"
            )
            return doc["text"]

        logger.info(f"Релевантные документы не найдены для {query!r}")
        return None

    except Exception as exc:
        logger.error(
            f"Ошибка при выполнении RAG-поиска для {query!r}: {exc}",
            exc_info=True
        )
        return None


def add_document(content: str, file_path: str) -> bool:
    """Добавляет документ в существующую коллекцию"""
    document = Document(
        page_content=content,
        metadata={
            "source": str(file_path),
            "filename": Path(file_path).name
        }
    )

    try:
        vector_store.add_documents([document])
        logger.info(f"Документ добавлен в RAG: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка добавления документа в RAG: {e}")
        return False


async def generate_document_background(query: str):
    """Фоновая задача для генерации документа"""
    try:
        # Все тяжелые операции здесь
        content = await asyncio.to_thread(
            generate_and_validate_documentation, query
        )

        if not content.strip().startswith('###'):
            logger.error(f'Неверный формат документа для запроса: {query}')
            return

        file_path = await asyncio.to_thread(save_document, content, query)
        added = await asyncio.to_thread(add_document, content, file_path)

        if added:
            logger.info(f"Документ создан и добавлен в RAG: {file_path}")
        else:
            logger.warning(f"Документ не был добавлен в RAG: {file_path}")

    except Exception as e:
        logger.error(f'Ошибка фоновой генерации: {e}', exc_info=True)

"""
Builds, persists, and queries the local Chroma collection. Depends on
chunking.py and embeddings.py, but nothing here talks to FastAPI, the
in-memory store, or routers — following the same separation of concerns
as the rest of ai/.
"""

from langchain_chroma import Chroma
from langchain_core.documents import Document as LCDocument

from app.ai.chunking import documents_to_chunks
from app.ai.embeddings import get_embeddings
from app.core.config import settings
from app.models.document import Document


def build_vector_store(
    documents: list[Document], persist_directory: str | None = None
) -> Chroma:
    """
    Chunks, embeds, and persists the given documents to a fresh (or
    appended-to) Chroma collection on disk. Passing persist_directory here
    is enough — writes land on disk as they happen, no separate .persist().
    """
    directory = persist_directory or str(settings.chroma_persist_dir)
    chunks = documents_to_chunks(documents)
    return Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        persist_directory=directory,
    )


def load_vector_store(persist_directory: str | None = None) -> Chroma:
    """Reopens an existing Chroma collection without re-chunking or re-embedding."""
    directory = persist_directory or str(settings.chroma_persist_dir)
    return Chroma(
        persist_directory=directory,
        embedding_function=get_embeddings(),
    )


def search_documents(
    query: str, k: int = 3, category: str | None = None
) -> list[LCDocument]:
    """Searches the already-persisted collection — never rebuilds it."""
    vector_store = load_vector_store()
    if category is not None:
        return vector_store.similarity_search(query, k=k, filter={"category": category})
    return vector_store.similarity_search(query, k=k)
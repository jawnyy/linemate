from functools import lru_cache
from pathlib import Path

from app.ai.memory import ConversationMemory, memory
from app.ai.vector_store import build_vector_store
from app.core.config import settings
from app.core.store import InMemoryStore, store
from app.ingestion.crew_loader import load_crew_from_csv
from app.ingestion.document_loader import load_documents_from_csv
from app.ingestion.ticket_loader import load_tickets_from_csv


@lru_cache
def _load_store() -> InMemoryStore:
    """
    Populates the shared in-memory store from the three seed CSVs exactly
    once. lru_cache means every request's Depends(get_store) after the first
    reuses this same populated store instead of re-reading disk each time.
    """
    for document in load_documents_from_csv(settings.documents_csv_path):
        store.add_document(document)
    for ticket in load_tickets_from_csv(settings.tickets_csv_path):
        store.add_ticket(ticket)
    for crew_member in load_crew_from_csv(settings.crew_csv_path):
        store.add_crew_member(crew_member)
    return store


def get_store() -> InMemoryStore:
    return _load_store()


def get_memory() -> ConversationMemory:
    return memory


@lru_cache
def _ensure_vector_store() -> None:
    """
    Builds the Chroma collection from the current store's documents exactly
    once per process, and only if it doesn't already exist on disk. Chroma
    persists to settings.chroma_persist_dir, so once a prior run has built
    it, later process starts skip straight past this -- ask_question() just
    calls search_documents(), which reopens the existing collection via
    load_vector_store() instead of re-chunking/re-embedding everything again.
    """
    persist_dir = Path(settings.chroma_persist_dir)
    if not persist_dir.exists() or not any(persist_dir.iterdir()):
        build_vector_store(get_store().list_documents())


def ensure_vector_store() -> None:
    _ensure_vector_store()
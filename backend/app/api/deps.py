from functools import lru_cache

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
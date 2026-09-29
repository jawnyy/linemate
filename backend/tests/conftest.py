from datetime import date, datetime, timedelta
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_store
from app.api.main import app
from app.core.config import settings
from app.core.store import InMemoryStore
from app.models import (
    CrewMember,
    CrewStation,
    Document,
    DocumentCategory,
    Ticket,
    TicketPriority,
    TicketStatus,
)

@pytest.fixture
def seeded_store() -> InMemoryStore:
    """
    A small, known dataset built by hand so every test's expected result is
    computable by inspection, independent of whatever the real CSVs contain.
    """
    test_store = InMemoryStore()

    # --- Crew ---
    grill_cook = CrewMember(1, "Test Grill Cook", CrewStation.GRILL)
    pastry_cook = CrewMember(2, "Test Pastry Cook", CrewStation.PASTRY)
    for crew_member in (grill_cook, pastry_cook):
        test_store.add_crew_member(crew_member)

    # --- Documents ---
    stale_doc = Document(
        101,
        "Stale Grill SOP",
        DocumentCategory.SOP,
        "Body text for the stale SOP.",
        owner_id=grill_cook.id,
        last_reviewed_at=date.today() - timedelta(days=365),
    )
    fresh_doc = Document(
        102,
        "Fresh Pastry Recipe",
        DocumentCategory.RECIPE,
        "Body text for the fresh recipe.",
        owner_id=pastry_cook.id,
        last_reviewed_at=date.today() - timedelta(days=5),
    )
    for document in (stale_doc, fresh_doc):
        test_store.add_document(document)

    # --- Tickets ---
    # 201: assigned to pastry_cook but related to a doc owned by grill_cook -> mismatch
    mismatched_ticket = Ticket(
        201,
        "Grill SOP needs a fix, wrongly assigned",
        TicketPriority.HIGH,
        assignee_id=pastry_cook.id,
        related_document_id=stale_doc.id,
        status=TicketStatus.OPEN,
        created_at=datetime.now(),
    )
    # 202: assigned to grill_cook, same station as the doc owner -> no mismatch
    matched_ticket = Ticket(
        202,
        "Grill SOP fix, correctly assigned",
        TicketPriority.MEDIUM,
        assignee_id=grill_cook.id,
        related_document_id=stale_doc.id,
        status=TicketStatus.OPEN,
        created_at=datetime.now(),
    )
    # 203: no related document, and already closed -> excluded from both checks
    unrelated_ticket = Ticket(
        203,
        "Front bar espresso machine leaking",
        TicketPriority.LOW,
        assignee_id=grill_cook.id,
        related_document_id=None,
        status=TicketStatus.CLOSED,
        created_at=datetime.now(),
    )
    for ticket in (mismatched_ticket, matched_ticket, unrelated_ticket):
        test_store.add_ticket(ticket)

    return test_store


@pytest.fixture
def client(seeded_store: InMemoryStore) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_store] = lambda: seeded_store
    test_client = TestClient(app, headers={"X-API-Key": settings.api_key})
    yield test_client
    app.dependency_overrides.clear()
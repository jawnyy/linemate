"""
Phase B analytics tests.

Two layers, same pattern as test_documents.py / test_tickets.py:

1. Unit tests call compute_station_workload / compute_document_ownership /
   find_station_mismatches directly with small hand-built lists — no FastAPI,
   no store, just the pure function. Data here is built to exercise cases the
   shared conftest.py `seeded_store` fixture doesn't happen to cover (an
   overloaded station, an Incident Report old enough to be "stale" but
   excluded anyway).
2. Integration tests hit /analytics/workload and /analytics/ownership through
   the `client` fixture, which already wires the real seeded_store from
   conftest.py in via dependency_overrides — same fixture test_tickets.py
   uses for /tickets/mismatches, so results here should agree with those.
"""
from datetime import date, timedelta

import pytest

from app.analytics.ownership import compute_document_ownership, find_station_mismatches
from app.analytics.workload import compute_station_workload
from app.models import (
    CrewMember,
    CrewStation,
    Document,
    DocumentCategory,
    Ticket,
    TicketPriority,
    TicketStatus,
)


# ---------------------------------------------------------------------------
# Unit tests: compute_station_workload
# ---------------------------------------------------------------------------

def test_compute_station_workload_flags_the_overloaded_station():
    crew = [
        CrewMember(1, "Grill Cook", CrewStation.GRILL),
        CrewMember(2, "Pastry Cook", CrewStation.PASTRY),
        CrewMember(3, "Prep Cook", CrewStation.PREP),
    ]

    tickets = [
        # Grill: 3 open tickets, heavy priority -> load 4 + 4 + 3 = 11
        Ticket(1, "t1", TicketPriority.CRITICAL, assignee_id=1, status=TicketStatus.OPEN),
        Ticket(2, "t2", TicketPriority.CRITICAL, assignee_id=1, status=TicketStatus.OPEN),
        Ticket(3, "t3", TicketPriority.HIGH, assignee_id=1, status=TicketStatus.IN_PROGRESS),
        # Pastry: 1 light ticket -> load 1
        Ticket(4, "t4", TicketPriority.LOW, assignee_id=2, status=TicketStatus.OPEN),
        # Prep: 1 medium ticket -> load 2
        Ticket(5, "t5", TicketPriority.MEDIUM, assignee_id=3, status=TicketStatus.OPEN),
        # Closed ticket on Grill must NOT count toward load, even at Critical
        Ticket(6, "t6", TicketPriority.CRITICAL, assignee_id=1, status=TicketStatus.CLOSED),
    ]

    report = compute_station_workload(tickets, crew)

    assert report["total_open_tickets"] == 5  # excludes the closed ticket

    by_station = {s["station"]: s for s in report["stations"]}
    assert set(by_station) == {"Grill", "Pastry", "Prep"}

    assert by_station["Grill"]["open_ticket_count"] == 3
    assert by_station["Grill"]["load_score"] == 11
    assert by_station["Grill"]["is_overloaded"] is True

    assert by_station["Pastry"]["load_score"] == 1
    assert by_station["Pastry"]["is_overloaded"] is False

    assert by_station["Prep"]["load_score"] == 2
    assert by_station["Prep"]["is_overloaded"] is False

    # share_pct should sum to ~100 across stations
    total_share = sum(s["load_share_pct"] for s in report["stations"])
    assert total_share == pytest.approx(100.0)

    assert report["mean_load_score"] == pytest.approx(14 / 3)


def test_compute_station_workload_empty_input_does_not_crash():
    report = compute_station_workload([], [])
    assert report["stations"] == []
    assert report["total_open_tickets"] == 0
    assert report["mean_load_score"] == 0.0
    assert report["std_load_score"] == 0.0


# ---------------------------------------------------------------------------
# Unit tests: compute_document_ownership
# ---------------------------------------------------------------------------

def test_compute_document_ownership_excludes_incident_reports_from_staleness():
    crew = {
        1: CrewMember(1, "Grill Cook", CrewStation.GRILL),
        2: CrewMember(2, "Pastry Cook", CrewStation.PASTRY),
    }

    today = date.today()
    documents = {
        # Grill owns 3: one genuinely stale, one fresh, one "old" Incident
        # Report that must NOT count as stale despite being older than both.
        101: Document(101, "Old SOP", DocumentCategory.SOP, "body",
                      owner_id=1, last_reviewed_at=today - timedelta(days=200)),
        102: Document(102, "Fresh Recipe", DocumentCategory.RECIPE, "body",
                      owner_id=1, last_reviewed_at=today - timedelta(days=10)),
        103: Document(103, "Old Incident Report", DocumentCategory.INCIDENT_REPORT, "body",
                      owner_id=1, last_reviewed_at=today - timedelta(days=400)),
        # Pastry owns 1, fresh
        104: Document(104, "Fresh Onboarding Doc", DocumentCategory.ONBOARDING,
                      "body", owner_id=2, last_reviewed_at=today - timedelta(days=5)),
    }

    report = compute_document_ownership(documents, crew, threshold=90)

    assert report["total_documents"] == 4

    by_station = {s["station"]: s for s in report["stations"]}

    grill = by_station["Grill"]
    assert grill["owned_document_count"] == 3
    assert grill["stale_document_count"] == 1  # only doc 101, not the Incident Report
    assert grill["stale_share_pct"] == pytest.approx(33.33, rel=1e-3)
    assert grill["is_stale_risk"] is False  # 1/3 is not > 50%

    pastry = by_station["Pastry"]
    assert pastry["owned_document_count"] == 1
    assert pastry["stale_document_count"] == 0
    assert pastry["is_stale_risk"] is False


def test_compute_document_ownership_flags_stale_risk_over_50_percent():
    crew = {1: CrewMember(1, "Grill Cook", CrewStation.GRILL)}
    today = date.today()
    documents = {
        201: Document(201, "Stale 1", DocumentCategory.SOP, "body",
                      owner_id=1, last_reviewed_at=today - timedelta(days=200)),
        202: Document(202, "Stale 2", DocumentCategory.RECIPE, "body",
                      owner_id=1, last_reviewed_at=today - timedelta(days=300)),
        203: Document(203, "Fresh", DocumentCategory.RECIPE, "body",
                      owner_id=1, last_reviewed_at=today - timedelta(days=5)),
    }

    report = compute_document_ownership(documents, crew, threshold=90)

    grill = report["stations"][0]
    assert grill["stale_document_count"] == 2
    assert grill["owned_document_count"] == 3
    assert grill["is_stale_risk"] is True  # 2/3 > 50%


def test_compute_document_ownership_skips_documents_with_unknown_owner():
    # owner_id 999 doesn't exist in crew -> document should be silently ignored,
    # not crash.
    crew = {1: CrewMember(1, "Grill Cook", CrewStation.GRILL)}
    documents = {
        301: Document(301, "Orphaned Doc", DocumentCategory.SOP, "body",
                      owner_id=999, last_reviewed_at=date.today()),
    }

    report = compute_document_ownership(documents, crew, threshold=90)

    assert report["stations"] == []
    assert report["total_documents"] == 1  # counts all documents, regardless of owner


# ---------------------------------------------------------------------------
# Unit tests: find_station_mismatches
# ---------------------------------------------------------------------------

def test_find_station_mismatches_only_flags_open_tickets_with_dangling_owner_handled():
    crew = {
        1: CrewMember(1, "Grill Cook", CrewStation.GRILL),
        2: CrewMember(2, "Pastry Cook", CrewStation.PASTRY),
    }
    documents = {
        101: Document(101, "Grill SOP", DocumentCategory.SOP, "body",
                      owner_id=1, last_reviewed_at=date.today()),
    }
    tickets = [
        # Real mismatch: assignee is Pastry, doc owner is Grill, status OPEN
        Ticket(1, "mismatch", TicketPriority.HIGH, assignee_id=2,
               related_document_id=101, status=TicketStatus.OPEN),
        # Same mismatch shape but IN_PROGRESS -> must be excluded (strict OPEN only)
        Ticket(2, "in-progress-mismatch", TicketPriority.HIGH, assignee_id=2,
               related_document_id=101, status=TicketStatus.IN_PROGRESS),
        # No related_document_id -> skipped, not crashed
        Ticket(3, "no-doc", TicketPriority.LOW, assignee_id=1,
               related_document_id=None, status=TicketStatus.OPEN),
        # Dangling related_document_id -> skipped, not crashed
        Ticket(4, "dangling-doc", TicketPriority.LOW, assignee_id=1,
               related_document_id=9999, status=TicketStatus.OPEN),
    ]

    mismatches = find_station_mismatches(tickets, documents, crew)

    assert len(mismatches) == 1
    assert mismatches[0].ticket.id == 1
    assert mismatches[0].assignee.station == CrewStation.PASTRY
    assert mismatches[0].owner.station == CrewStation.GRILL


# ---------------------------------------------------------------------------
# Integration tests: /analytics/workload and /analytics/ownership
# Reuses the same seeded_store fixture as test_tickets.py's mismatch tests,
# so results here should be consistent with those.
# ---------------------------------------------------------------------------

def test_workload_endpoint_matches_seeded_store(client):
    # seeded_store: ticket 201 (Pastry, HIGH, OPEN), 202 (Grill, MEDIUM, OPEN),
    # 203 (Grill, LOW, CLOSED -> excluded).
    response = client.get("/analytics/workload")
    assert response.status_code == 200

    body = response.json()
    assert body["total_open_tickets"] == 2

    by_station = {s["station"]: s for s in body["stations"]}
    assert by_station["Pastry"]["load_score"] == 3  # HIGH
    assert by_station["Grill"]["load_score"] == 2  # MEDIUM


def test_ownership_endpoint_matches_seeded_store(client):
    # seeded_store: stale_doc (101, Grill, ~365 days old), fresh_doc (102,
    # Pastry, ~5 days old). Explicit threshold keeps this independent of
    # whatever settings.staleness_threshold_days currently defaults to.
    response = client.get("/analytics/ownership", params={"threshold": 90})
    assert response.status_code == 200

    body = response.json()
    assert body["total_documents"] == 2

    by_station = {s["station"]: s for s in body["stations"]}
    assert by_station["Grill"]["stale_document_count"] == 1
    assert by_station["Grill"]["is_stale_risk"] is True
    assert by_station["Pastry"]["stale_document_count"] == 0
    assert by_station["Pastry"]["is_stale_risk"] is False


def test_analytics_endpoints_require_api_key(client):
    response = client.get("/analytics/workload", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401

    response = client.get("/analytics/ownership", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401
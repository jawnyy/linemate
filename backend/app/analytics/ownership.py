from typing import NamedTuple

from app.core.config import settings
from app.models import CrewMember, Document, DocumentCategory, Ticket, TicketStatus

class StationMismatch(NamedTuple):
    ticket: Ticket
    document: Document
    assignee: CrewMember
    owner: CrewMember

def find_station_mismatches(
    tickets: list[Ticket],
    documents: dict[int, Document],
    crew: dict[int, CrewMember],
) -> list[StationMismatch]:
    mismatches: list[StationMismatch] = []

    for ticket in tickets:
        if ticket.status != TicketStatus.OPEN or ticket.related_document_id is None:
            continue

        document = documents.get(ticket.related_document_id)
        assignee = crew.get(ticket.assignee_id)
        if document is None or assignee is None:
            continue

        owner = crew.get(document.owner_id)
        if owner is None:
            continue

        if assignee.station != owner.station:
            mismatches.append(StationMismatch(ticket, document, assignee, owner))

    return mismatches


def compute_document_ownership(
    documents: dict[int, Document],
    crew: dict[int, CrewMember],
    threshold: int | None = None,
) -> dict:
    """
    Per-station rollup: how many documents each station owns, and how many
    of those are stale (excluding Incident Reports, same rule as /documents/stale).
    """
    limit = threshold if threshold is not None else settings.staleness_threshold_days

    station_totals: dict[str, int] = {}
    station_stale: dict[str, int] = {}

    for document in documents.values():
        owner = crew.get(document.owner_id)
        if owner is None:
            continue

        station = owner.station.value
        station_totals[station] = station_totals.get(station, 0) + 1

        is_stale = (
            document.category != DocumentCategory.INCIDENT_REPORT
            and document.is_stale(limit)
        )
        if is_stale:
            station_stale[station] = station_stale.get(station, 0) + 1

    stations = [
        {
            "station": station,
            "owned_document_count": total,
            "stale_document_count": station_stale.get(station, 0),
            "stale_share_pct": (
                round(station_stale.get(station, 0) / total * 100, 2) if total else 0.0
            ),
            "is_stale_risk": station_stale.get(station, 0) / total > 0.5 if total else False,
        }
        for station, total in station_totals.items()
    ]

    return {
        "stations": stations,
        "total_documents": len(documents),
    }
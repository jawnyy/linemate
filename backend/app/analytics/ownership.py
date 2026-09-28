from typing import NamedTuple

from app.models import CrewMember, Document, Ticket, TicketStatus

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
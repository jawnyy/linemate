# app/core/store.py
from app.models import Document, Ticket, CrewMember
from app.core.exceptions import (
    DocumentNotFoundError,
    TicketNotFoundError,
    CrewMemberNotFoundError,
)


class InMemoryStore:
    def __init__(self):
        self.documents: dict[int, Document] = {}
        self.tickets: dict[int, Ticket] = {}
        self.crew_members: dict[int, CrewMember] = {}

    # --- Documents ---
    def add_document(self, doc: Document) -> None:
        self.documents[doc.id] = doc

    def get_document(self, doc_id: int) -> Document:
        if doc_id not in self.documents:
            raise DocumentNotFoundError(doc_id)
        return self.documents[doc_id]

    def list_documents(self) -> list[Document]:
        return list(self.documents.values())

    # --- Tickets ---
    def add_ticket(self, ticket: Ticket) -> None:
        self.tickets[ticket.id] = ticket

    def get_ticket(self, ticket_id: int) -> Ticket:
        if ticket_id not in self.tickets:
            raise TicketNotFoundError(ticket_id)
        return self.tickets[ticket_id]

    def list_tickets(self) -> list[Ticket]:
        return list(self.tickets.values())

    # --- Crew ---
    def add_crew_member(self, crew: CrewMember) -> None:
        self.crew_members[crew.id] = crew

    def get_crew_member(self, crew_id: int) -> CrewMember:
        if crew_id not in self.crew_members:
            raise CrewMemberNotFoundError(crew_id)
        return self.crew_members[crew_id]

    def list_crew_members(self) -> list[CrewMember]:
        return list(self.crew_members.values())

store = InMemoryStore()
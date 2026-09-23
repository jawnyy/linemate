from datetime import datetime
from typing import ClassVar

from .enums import TicketPriority, TicketStatus

class Ticket:

    registry: ClassVar[list["Ticket"]] = []

    def __init__(self, id: int, title: str, priority: TicketPriority,
                 assignee_id: int, related_document_id: int | None = None,
                 status: TicketStatus = TicketStatus.OPEN,
                 created_at: datetime | None = None):
        self.id = id
        self.title = title
        self.priority = priority
        self.status = status
        self.assignee_id = assignee_id
        self.related_document_id = related_document_id
        self.created_at = created_at or datetime.now()
        Ticket.registry.append(self)

    def resolve(self) -> None:
        self.status = TicketStatus.RESOLVED

    def close(self) -> None:
        self.status = TicketStatus.CLOSED

    @classmethod
    def get_by_id(cls, ticket_id: int) -> "Ticket | None":
        for ticket in cls.registry:
            if ticket.id == ticket_id:
                return ticket
        return None

    def __repr__(self) -> str:
        return (f"Ticket(id={self.id}, title={self.title!r}, "
                f"priority={self.priority.value}, status={self.status.value})")
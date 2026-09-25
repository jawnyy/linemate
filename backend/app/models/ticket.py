from datetime import datetime

from .enums import TicketPriority, TicketStatus

class Ticket:
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

    def resolve(self) -> None:
        self.status = TicketStatus.RESOLVED

    def close(self) -> None:
        self.status = TicketStatus.CLOSED

    def __repr__(self) -> str:
        return (f"Ticket(id={self.id}, title={self.title!r}, "
                f"priority={self.priority.value}, status={self.status.value})")
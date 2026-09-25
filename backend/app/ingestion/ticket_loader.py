import csv
from datetime import datetime
from pathlib import Path

from app.core.exceptions import TicketLoadError
from app.models import Ticket, TicketPriority, TicketStatus


def _row_to_ticket(row: dict[str, str]) -> Ticket:
    try:
        priority = TicketPriority(row["priority"])
    except ValueError as exc:
        raise TicketLoadError(f"row {row.get('id')}: invalid priority {row['priority']!r}") from exc

    try:
        status = TicketStatus(row["status"])
    except ValueError as exc:
        raise TicketLoadError(f"row {row.get('id')}: invalid status {row['status']!r}") from exc

    try:
        ticket_id = int(row["id"])
        assignee_id = int(row["assignee_id"])
        # only a blank, non-integer value should raise an error
        related_document_id = (
            int(row["related_document_id"]) if row["related_document_id"] else None
        )
    except ValueError as exc:
        raise TicketLoadError(
            f"row {row.get('id')}: id/assignee_id/related_document_id must be integers."
        ) from exc

    created_at = (
        datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None
    )

    return Ticket(
        ticket_id,
        row["title"],
        priority,
        assignee_id=assignee_id,
        related_document_id=related_document_id,
        status=status,
        created_at=created_at,
    )


def load_tickets_from_csv(csv_path: str | Path) -> list[Ticket]:
    tickets: list[Ticket] = []
    with open(csv_path, newline="", encoding="utf-8") as handle:
        # DictReader turns each row into a dict keyed by the header row, so
        # row["priority"] reads clearer than row[2]
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                tickets.append(_row_to_ticket(row))
            except TicketLoadError as exc:
                print(f" SKIPPED {exc}")

    return tickets
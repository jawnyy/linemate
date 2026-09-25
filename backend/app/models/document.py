from datetime import date
from typing import ClassVar

from .enums import DocumentCategory

class Document:

    STALE_THRESHOLD_DAYS: ClassVar[int] = 90

    def __init__(self, id: int, title: str, category: DocumentCategory, body: str, owner_id: int, last_reviewed_at: date):
        self.id = id
        self.title = title
        self.category = category
        self.body = body
        self.owner_id = owner_id
        self.last_reviewed_at = last_reviewed_at or date.today()

    def days_since_last_reviewed(self, as_of: date | None = None) -> int:
        today = as_of or date.today()
        return (today - self.last_reviewed_at).days

    def is_stale(self, threshold: int | None = None, as_of: date | None = None) -> bool:
        limit = threshold if threshold is not None else Document.STALE_THRESHOLD_DAYS
        return self.days_since_last_reviewed(as_of) > limit

    def __repr__(self) -> str:
        return (f"Document(id={self.id}, title={self.title!r}, "
                f"category={self.category.value}, "
                f"last_reviewed_at={self.last_reviewed_at.isoformat()})")
    
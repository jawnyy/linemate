from datetime import datetime

class Comment:
    def __init__(self, id: int, ticket_id: int, author_id: int,
                 body: str, created_at: datetime | None = None):
        self.id = id
        self.ticket_id = ticket_id
        self.author_id = author_id
        self.body = body
        self.created_at = created_at or datetime.now()

    def __repr__(self) -> str:
        return (f"Comment(id={self.id}, ticket_id={self.ticket_id}, "
                f"author_id={self.author_id})")
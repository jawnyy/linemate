from app.api.schemas import StaleDocumentOut
from app.models import Document, DocumentCategory


def find_stale_documents(
    documents: list[Document], threshold: int
) -> list[StaleDocumentOut]:
    """Stale Documentation business question: non-Incident-Report docs past the review threshold."""
    return [
        StaleDocumentOut(
            id=d.id,
            title=d.title,
            category=d.category,
            days_since_last_reviewed=d.days_since_last_reviewed(),
        )
        for d in documents
        if d.category != DocumentCategory.INCIDENT_REPORT and d.is_stale(threshold)
    ]
import csv
from datetime import date
from pathlib import Path

from app.core.exceptions import DocumentLoadError
from app.models import Document, DocumentCategory


def _row_to_document(row: dict[str, str]) -> Document:
    try:
        category = DocumentCategory(row["category"])
    except ValueError as exc:
        raise DocumentLoadError(f"row {row.get('id')}: invalid category {row['category']!r}") from exc

    try:
        document_id = int(row["id"])
        owner_id = int(row["owner_id"])
    except ValueError as exc:
        raise DocumentLoadError(
            f"row {row.get('id')}: id/owner_id must be integers."
        ) from exc

    try:
        last_reviewed_at = date.fromisoformat(row["last_reviewed_at"])
    except ValueError as exc:
        raise DocumentLoadError(
            f"row {row.get('id')}: last_reviewed_at must be an ISO date (YYYY-MM-DD), "
            f"got {row['last_reviewed_at']!r}."
        ) from exc

    return Document(
        document_id,
        row["title"],
        category,
        row["body"],
        owner_id,
        last_reviewed_at,
    )


def load_documents_from_csv(csv_path: str | Path) -> list[Document]:
    documents: list[Document] = []
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                documents.append(_row_to_document(row))
            except DocumentLoadError as exc:
                print(f" SKIPPED {exc}")

    return documents
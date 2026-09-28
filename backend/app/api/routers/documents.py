from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.analytics.staleness import find_stale_documents
from app.api.deps import get_store
from app.api.schemas import DocumentDetailOut, DocumentOut, DocumentPage, StaleDocumentOut
from app.api.security import require_api_key
from app.core.config import settings
from app.core.exceptions import DocumentNotFoundError
from app.core.store import InMemoryStore

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(require_api_key)],
)


@router.get("", response_model=DocumentPage, status_code=status.HTTP_200_OK)
def list_documents(
    skip: int = Query(0, ge=0, description="Number of documents to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max documents to return"),
    store: InMemoryStore = Depends(get_store),
) -> DocumentPage:
    all_documents = store.list_documents()
    page = all_documents[skip : skip + limit]

    return DocumentPage(
        items=[DocumentOut.model_validate(d) for d in page],
        total=len(all_documents),
        skip=skip,
        limit=limit,
    )

@router.get("/stale", response_model=list[StaleDocumentOut])
def list_stale_documents(
    threshold: int = Query(settings.staleness_threshold_days, ge=0),
    store: InMemoryStore = Depends(get_store),
) -> list[StaleDocumentOut]:
    return find_stale_documents(store.list_documents(), threshold)


@router.get("/{document_id}", response_model=DocumentDetailOut)
def get_document(
    document_id: int,
    store: InMemoryStore = Depends(get_store),
) -> DocumentDetailOut:
    try:
        document = store.get_document(document_id)
    except DocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )
    return DocumentDetailOut.model_validate(document)
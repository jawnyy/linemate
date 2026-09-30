from langchain_core.documents import Document as LCDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.models.document import Document

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap,
)


def _document_to_metadata(document: Document) -> dict:
    """
    Chroma's underlying client only accepts str/int/float/bool metadata —
    no None, no nested dicts, no lists. last_reviewed_at is a plain Python
    date on our model, so it gets stringified here.
    """
    return {
        "document_id": document.id,
        "title": document.title,
        "category": document.category.value,
        "last_reviewed_at": document.last_reviewed_at.isoformat(),
    }


def documents_to_chunks(documents: list[Document]) -> list[LCDocument]:
    lc_documents = [
        LCDocument(page_content=document.body, metadata=_document_to_metadata(document))
        for document in documents
    ]
    return _splitter.split_documents(lc_documents)
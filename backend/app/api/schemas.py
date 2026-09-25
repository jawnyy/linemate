from datetime import date
from pydantic import BaseModel, ConfigDict

from app.models import DocumentCategory, TicketPriority, TicketStatus, CrewStation


# --- Documents ---
class DocumentOut(BaseModel):
    """Lean shape for list views — excludes body (recipes/SOPs can be long)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: DocumentCategory
    owner_id: int
    last_reviewed_at: date


class DocumentDetailOut(BaseModel):
    """Full shape for single-document views — includes body."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: DocumentCategory
    body: str
    owner_id: int
    last_reviewed_at: date


class StaleDocumentOut(BaseModel):
    id: int
    title: str
    category: DocumentCategory
    days_since_last_reviewed: int


# --- Tickets ---
class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    priority: TicketPriority
    status: TicketStatus
    assignee_id: int
    related_document_id: int | None


# --- Station Ownership Mismatch ---
class MismatchOut(BaseModel):
    ticket_id: int
    ticket_title: str
    document_id: int
    document_title: str
    assignee_name: str
    assignee_station: CrewStation
    owner_name: str
    owner_station: CrewStation


# --- Pagination envelope ---
class DocumentPage(BaseModel):
    items: list[DocumentOut]
    total: int
    skip: int
    limit: int


class TicketPage(BaseModel):
    items: list[TicketOut]
    total: int
    skip: int
    limit: int


# --- Station Workload Distribution ---
class StationWorkload(BaseModel):
    station: CrewStation
    open_ticket_count: int
    load_score: int
    load_share_pct: float
    is_overloaded: bool


class WorkloadReport(BaseModel):
    stations: list[StationWorkload]
    total_open_tickets: int
    mean_load_score: float
    std_load_score: float


# --- Stale Documentation by Station ---
class StationDocumentOwnership(BaseModel):
    station: CrewStation
    owned_document_count: int
    stale_document_count: int
    stale_share_pct: float
    is_stale_risk: bool


class DocumentOwnershipReport(BaseModel):
    stations: list[StationDocumentOwnership]
    total_documents: int
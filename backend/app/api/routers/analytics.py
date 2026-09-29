from fastapi import APIRouter, Depends, Query, status

from app.analytics.ownership import compute_document_ownership
from app.analytics.workload import compute_station_workload
from app.api.deps import get_store
from app.api.schemas import DocumentOwnershipReport, WorkloadReport
from app.api.security import require_api_key
from app.core.config import settings
from app.core.store import InMemoryStore

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(require_api_key)],
)


@router.get("/workload", response_model=WorkloadReport, status_code=status.HTTP_200_OK)
def get_workload_report(
    store: InMemoryStore = Depends(get_store),
) -> WorkloadReport:
    # compute_station_workload takes list[Ticket]/list[CrewMember], not dicts
    report = compute_station_workload(store.list_tickets(), store.list_crew_members())
    return WorkloadReport(**report)


@router.get("/ownership", response_model=DocumentOwnershipReport, status_code=status.HTTP_200_OK)
def get_ownership_report(
    threshold: int = Query(settings.staleness_threshold_days, ge=0),
    store: InMemoryStore = Depends(get_store),
) -> DocumentOwnershipReport:
    # compute_document_ownership takes dict[int, Document]/dict[int, CrewMember]
    report = compute_document_ownership(store.documents, store.crew_members, threshold)
    return DocumentOwnershipReport(**report)
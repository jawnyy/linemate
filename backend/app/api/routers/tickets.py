from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.analytics.ownership import find_station_mismatches
from app.api.deps import get_store
from app.api.schemas import MismatchOut, TicketOut, TicketPage
from app.api.security import require_api_key
from app.core.exceptions import TicketNotFoundError
from app.core.store import InMemoryStore

router = APIRouter(
    prefix="/tickets",
    tags=["tickets"],
    dependencies=[Depends(require_api_key)],
)

@router.get("", response_model=TicketPage, status_code=status.HTTP_200_OK)
def list_tickets(
    skip: int = Query(0, ge=0, description="Number of tickets to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max tickets to return"),
    store: InMemoryStore = Depends(get_store),
) -> TicketPage:
    all_tickets = store.list_tickets()
    page = all_tickets[skip : skip + limit]

    return TicketPage(
        items=[TicketOut.model_validate(t) for t in page],
        total=len(all_tickets),
        skip=skip,
        limit=limit,
    )

@router.get("/mismatches", response_model=list[MismatchOut])
def list_station_mismatches(
    store: InMemoryStore = Depends(get_store),
) -> list[MismatchOut]:
    return [
        MismatchOut(
            ticket_id=m.ticket.id,
            ticket_title=m.ticket.title,
            document_id=m.document.id,
            document_title=m.document.title,
            assignee_name=m.assignee.name,
            assignee_station=m.assignee.station,
            owner_name=m.owner.name,
            owner_station=m.owner.station,
        )
        for m in find_station_mismatches(
            store.list_tickets(), store.documents, store.crew_members
        )
    ]

@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(
    ticket_id: int,
    store: InMemoryStore = Depends(get_store),
) -> TicketOut:
    try:
        ticket = store.get_ticket(ticket_id)
    except TicketNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No ticket with id {ticket_id} found",
        )
    return TicketOut.model_validate(ticket)
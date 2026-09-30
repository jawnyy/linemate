"""
/ask endpoint: Grounded Q&A over Hearthline's document corpus.

Wires together chains.ask_question() (stateless retrieval + LLM answer) and
memory.py (per-session history), behind the same API key dependency as every
other router. ensure_vector_store() guarantees the Chroma collection exists
before the first real request ever calls search_documents() against it.
"""
from fastapi import APIRouter, Depends, status

from app.ai.chains import ask_question
from app.ai.memory import ConversationMemory
from app.api.deps import ensure_vector_store, get_memory
from app.api.schemas import AskRequest, AskResponse, CitationOut
from app.api.security import require_api_key

router = APIRouter(
    prefix="/ask",
    tags=["ask"],
    dependencies=[Depends(require_api_key), Depends(ensure_vector_store)],
)


@router.post("", response_model=AskResponse, status_code=status.HTTP_200_OK)
def ask(
    request: AskRequest,
    memory: ConversationMemory = Depends(get_memory),
) -> AskResponse:
    history = memory.get_history(request.session_id)

    result = ask_question(request.question, history)

    memory.add_turn(request.session_id, request.question, result["answer"])

    return AskResponse(
        answer=result["answer"],
        citations=[CitationOut(**citation) for citation in result["citations"]],
    )
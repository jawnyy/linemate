"""
LCEL chains for LineMate: retrieval-grounded Q&A over Hearthline's kitchen
documents, with citations and conversation memory.

Nothing in this file talks to FastAPI or the in-memory store directly for
retrieval — it only reads from the Chroma index via vectorstore.py.
"""
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama

from app.ai.vector_store import search_documents
from app.core.config import settings

# One shared ChatOllama instance for this entire module.
_llm = ChatOllama(
    model=settings.llm_model,
    base_url=settings.ollama_base_url,
    temperature=0.2,
)

_qa_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are LineMate, an internal kitchen operations assistant for "
        "Hearthline. Answer the question using only the context below, "
        "drawn from Hearthline's own documents. If the context doesn't "
        "contain the answer, say so plainly. Do not invent details.\n\n"
        "Context:\n{context}"
    ),
    MessagesPlaceholder("history"),
    ("human", "{question}"),
])

_qa_chain = _qa_prompt | _llm | StrOutputParser()


def _format_context(results) -> str:
    """Turns retrieved chunks into a labeled context block the prompt can cite from."""
    return "\n\n".join(
        f"[{r.metadata['document_id']}] {r.metadata['title']}: {r.page_content}"
        for r in results
    )


def _build_citations(results) -> list[dict]:
    """Deduplicated citation list — one entry per source document, not per chunk."""
    seen = {}
    for r in results:
        doc_id = r.metadata["document_id"]
        if doc_id not in seen:
            seen[doc_id] = {"document_id": doc_id, "title": r.metadata["title"]}
    return list(seen.values())


def ask_question(question: str, history: list[BaseMessage], k: int = 3) -> dict:
    """
    Stateless, testable entry point: retrieve relevant chunks, answer using
    them, return both the answer and the citations it drew from.
    `history` is owned and appended to by the caller (same pattern as the
    reference file's follow-up chains) — this function doesn't persist anything.
    """
    results = search_documents(question, k=k)
    context = _format_context(results)

    answer = _qa_chain.invoke({
        "context": context,
        "history": history,
        "question": question,
    })

    return {
        "answer": answer,
        "citations": _build_citations(results),
    }
"""
Phase C AI-layer tests.

Two tiers:

1. Pure unit tests -- chunking.py, memory.py, and chains.py's private
   _build_citations()/_format_context() helpers. None of these touch Ollama
   or Chroma, so they always run, fast and deterministic.
2. A small live-Ollama tier for ask_question() itself -- this is the one
   thing that genuinely can't be tested without a real embedding + LLM call.
   Gated behind requires_ollama, which skips (not fails) if Ollama isn't
   reachable at settings.ollama_base_url, so `pytest` still passes clean in
   an environment where Ollama isn't running.
"""
import socket
from datetime import date
from urllib.parse import urlparse

import pytest
from langchain_core.documents import Document as LCDocument
from langchain_core.messages import AIMessage, HumanMessage

from app.ai.chains import _build_citations, _format_context, ask_question
from app.ai.chunking import documents_to_chunks
from app.ai.memory import ConversationMemory
from app.ai.vector_store import build_vector_store
from app.core.config import settings
from app.models import Document, DocumentCategory


# ---------------------------------------------------------------------------
# chunking.py -- pure text splitting, no I/O
# ---------------------------------------------------------------------------

def test_documents_to_chunks_short_body_stays_as_one_chunk():
    doc = Document(
        901, "Test SOP", DocumentCategory.SOP, "Short body text.",
        owner_id=1, last_reviewed_at=date(2026, 1, 1),
    )
    chunks = documents_to_chunks([doc])

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.page_content == "Short body text."
    assert chunk.metadata["document_id"] == 901
    assert chunk.metadata["title"] == "Test SOP"
    assert chunk.metadata["category"] == "SOP"
    assert chunk.metadata["last_reviewed_at"] == "2026-01-01"


def test_documents_to_chunks_splits_long_bodies():
    long_body = "This sentence repeats to force a chunk split. " * 40  # ~1920 chars
    doc = Document(
        902, "Long Doc", DocumentCategory.RECIPE, long_body,
        owner_id=1, last_reviewed_at=date.today(),
    )
    chunks = documents_to_chunks([doc])

    assert len(chunks) > 1
    assert all(chunk.metadata["document_id"] == 902 for chunk in chunks)
    assert all(len(chunk.page_content) <= settings.chunk_size for chunk in chunks)


def test_documents_to_chunks_keeps_metadata_distinct_across_documents():
    doc_a = Document(903, "Doc A", DocumentCategory.SOP, "Body A.",
                      owner_id=1, last_reviewed_at=date.today())
    doc_b = Document(904, "Doc B", DocumentCategory.RECIPE, "Body B.",
                      owner_id=2, last_reviewed_at=date.today())

    chunks = documents_to_chunks([doc_a, doc_b])

    ids = {chunk.metadata["document_id"] for chunk in chunks}
    assert ids == {903, 904}


def test_documents_to_chunks_empty_input_returns_empty_list():
    assert documents_to_chunks([]) == []


# ---------------------------------------------------------------------------
# chains.py -- _build_citations / _format_context, no Ollama needed since
# these operate on already-retrieved LangChain Document chunks, not on a
# live search.
# ---------------------------------------------------------------------------

def test_build_citations_deduplicates_by_document_not_by_chunk():
    # Same document contributes two chunks (e.g. a long SOP split in two);
    # citations should collapse that to one entry, not two.
    chunks = [
        LCDocument(page_content="chunk 1", metadata={"document_id": 901, "title": "Doc A"}),
        LCDocument(page_content="chunk 2", metadata={"document_id": 901, "title": "Doc A"}),
        LCDocument(page_content="chunk 3", metadata={"document_id": 902, "title": "Doc B"}),
    ]

    citations = _build_citations(chunks)

    assert len(citations) == 2
    assert {c["document_id"] for c in citations} == {901, 902}


def test_build_citations_empty_input_returns_empty_list():
    assert _build_citations([]) == []


def test_format_context_labels_each_chunk_with_its_document_id():
    chunks = [
        LCDocument(page_content="Some body text.", metadata={"document_id": 901, "title": "Doc A"}),
    ]

    context = _format_context(chunks)

    assert "[901]" in context
    assert "Doc A" in context
    assert "Some body text." in context


# ---------------------------------------------------------------------------
# memory.py -- ConversationMemory, plain Python, no Ollama needed
# ---------------------------------------------------------------------------

def test_get_history_starts_empty_for_a_new_session():
    memory = ConversationMemory()
    assert memory.get_history("session-1") == []


def test_add_turn_appends_human_then_ai_message():
    memory = ConversationMemory()
    memory.add_turn("session-1", "What's the cooler temp range?", "33-38F.")

    history = memory.get_history("session-1")
    assert len(history) == 2
    assert isinstance(history[0], HumanMessage)
    assert history[0].content == "What's the cooler temp range?"
    assert isinstance(history[1], AIMessage)
    assert history[1].content == "33-38F."


def test_sessions_are_isolated_from_each_other():
    memory = ConversationMemory()
    memory.add_turn("session-a", "Q1", "A1")

    assert memory.get_history("session-a") != []
    assert memory.get_history("session-b") == []


def test_clear_removes_a_sessions_history():
    memory = ConversationMemory()
    memory.add_turn("session-1", "Q", "A")
    memory.clear("session-1")

    assert memory.get_history("session-1") == []


# ---------------------------------------------------------------------------
# /ask API-key gate -- exercises the router without touching the vector
# store at all, since require_api_key is listed before ensure_vector_store
# in ask.py's router-level dependencies and short-circuits on a bad key.
# No Ollama needed.
# ---------------------------------------------------------------------------

def test_ask_requires_api_key(client):
    response = client.post(
        "/ask",
        json={"session_id": "s1", "question": "test?"},
        headers={"X-API-Key": "wrong-key"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# ask_question() integration -- needs a real embedding model + LLM. Skips
# (doesn't fail) if Ollama isn't reachable, so the rest of the suite stays
# green without it running.
# ---------------------------------------------------------------------------

def _ollama_reachable(base_url: str, timeout: float = 1.0) -> bool:
    parsed = urlparse(base_url)
    try:
        with socket.create_connection((parsed.hostname, parsed.port or 11434), timeout=timeout):
            return True
    except OSError:
        return False


requires_ollama = pytest.mark.skipif(
    not _ollama_reachable(settings.ollama_base_url),
    reason=f"Ollama not reachable at {settings.ollama_base_url}; skipping live LLM/embedding tests.",
)


@pytest.fixture
def small_document_corpus() -> list[Document]:
    """
    Two short, hand-written, distinctly-topiced documents -- not the real
    documents.csv corpus. Keeps expected citations deterministic and
    independent of whatever the real seed data currently contains.
    """
    return [
        Document(
            901,
            "Test Espresso Machine Descaling SOP",
            DocumentCategory.SOP,
            "Descale the espresso machine every two weeks using a citric acid "
            "solution. Run three full cycles of clean water through the group "
            "head afterward to clear any residue before pulling shots for service.",
            owner_id=1,
            last_reviewed_at=date.today(),
        ),
        Document(
            902,
            "Test Walk-In Freezer Defrost Guide",
            DocumentCategory.SOP,
            "Defrost the walk-in freezer monthly. Remove all product to the "
            "backup freezer first, then run the manual defrost cycle for four "
            "hours before restocking.",
            owner_id=2,
            last_reviewed_at=date.today(),
        ),
    ]


@pytest.fixture
def isolated_vector_store(monkeypatch, tmp_path, small_document_corpus):
    """
    Points settings.chroma_persist_dir at a fresh pytest tmp_path and builds
    a vector store from small_document_corpus there -- so this never reads
    or writes the project's real chroma_db/, and each test starts clean.
    """
    monkeypatch.setattr(settings, "chroma_persist_dir", tmp_path)
    build_vector_store(small_document_corpus)


@requires_ollama
def test_ask_question_cites_the_correct_document_for_espresso_question(isolated_vector_store):
    result = ask_question("How often should the espresso machine be descaled?", history=[])

    assert result["answer"]
    citation_ids = {c["document_id"] for c in result["citations"]}
    assert 901 in citation_ids


@requires_ollama
def test_ask_question_cites_the_correct_document_for_freezer_question(isolated_vector_store):
    result = ask_question("How long does the walk-in freezer defrost cycle take?", history=[])

    assert result["answer"]
    citation_ids = {c["document_id"] for c in result["citations"]}
    assert 902 in citation_ids


@requires_ollama
def test_ask_question_uses_history_for_follow_up_context(isolated_vector_store):
    first = ask_question("How often should the espresso machine be descaled?", history=[])

    history = [
        HumanMessage(content="How often should the espresso machine be descaled?"),
        AIMessage(content=first["answer"]),
    ]
    # Deliberately ambiguous without the prior turn -- "it" only resolves via history.
    second = ask_question("What do I run through it afterward?", history=history)

    assert second["answer"]
    citation_ids = {c["document_id"] for c in second["citations"]}
    assert 901 in citation_ids
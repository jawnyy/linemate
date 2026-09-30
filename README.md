# LineMate

**LineMate** is an internal kitchen-operations assistant for
**Hearthline**, a fictional restaurant group. Kitchen managers can
browse documentation (recipes, SOPs, incident reports, onboarding
guides), track operational tickets, pull station-workload and
document-ownership analytics, and — the core of the project — ask
plain-language questions and get answers grounded in Hearthline's own
documents, with citations back to the source material and memory of
the conversation so far.

This project was built incrementally, one phase at a time. Everything
below describes it in its final, complete state.

## Features

- **A plain-Python OOP domain model** — `Document`, `Ticket`,
  `Comment`, and `CrewMember` classes with no framework dependency of
  their own.
- **CSV-based ingestion** — documents, tickets, and crew members each
  loaded from their own CSV, with per-row error handling so one bad
  row doesn't take down the whole batch.
- **A read-only REST API** (FastAPI + Pydantic v2) — routers,
  dependency injection, request-timing logging middleware, and an
  `X-API-Key` header required on every protected route. No
  create/update endpoints — this is a reporting and Q&A surface, not a
  system of record.
- **pandas/numpy analytics** — station workload distribution and
  document ownership/staleness reports computed directly from the
  in-memory data, no database involved.
- **Retrieval-augmented Q&A** (LangChain + Ollama + Chroma) — the
  document corpus is chunked, embedded, and persisted to a local
  vector store, built automatically on first use.
- **Grounded generation with citations** — questions are answered
  using only retrieved context, paired with a citation list resolved
  back to the specific source documents an answer drew from,
  deduplicated so multiple chunks from the same document collapse
  into a single citation.
- **Session-scoped conversation memory** — a hand-built per-session
  history store so a follow-up question can build on earlier turns of
  the same `/ask` conversation.
- **A `pytest` suite** — 40 tests spanning pure unit tests (analytics
  functions, chunking, citation/context logic, conversation memory)
  and `TestClient`-based integration tests for every router,
  including the API-key requirement itself.

## Tech Stack

| Layer | Technology |
|---|---|
| Language / runtime | Python 3.11+ |
| Web framework | FastAPI, Pydantic v2 |
| Testing | pytest, `fastapi.testclient.TestClient` |
| Analytics | pandas, numpy |
| LLM orchestration | LangChain (LCEL) |
| Chat model | Ollama, running `llama3.2` locally |
| Embeddings | Ollama, running `nomic-embed-text` locally |
| Vector store | Chroma (`langchain-chroma`), embedded/self-hosted mode |

Everything runs on localhost with no paid API keys, no cloud
deployment, and no external accounts — Ollama serves both the chat
model and the embedding model on your own machine.

## Project Structure

```
backend/
├── app/
│   ├── ai/
│   │   ├── chunking.py          # splits Document bodies into embeddable chunks
│   │   ├── embeddings.py        # Ollama embedding model wiring
│   │   ├── vectorstore.py       # build/load the Chroma collection, search_documents()
│   │   ├── chains.py            # LCEL retrieval + generation chain, citations
│   │   └── memory.py            # per-session conversation history
│   ├── analytics/
│   │   ├── staleness.py         # find_stale_documents()
│   │   ├── ownership.py         # find_station_mismatches(), compute_document_ownership()
│   │   └── workload.py          # compute_station_workload()
│   ├── api/
│   │   ├── deps.py              # store / memory / vector-store DI providers
│   │   ├── main.py              # FastAPI app, middleware, router registration
│   │   ├── schemas.py           # Pydantic request/response models
│   │   ├── security.py          # X-API-Key auth dependency
│   │   └── routers/
│   │       ├── documents.py     # /documents
│   │       ├── tickets.py       # /tickets
│   │       ├── analytics.py     # /analytics
│   │       └── ask.py           # /ask
│   ├── core/
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── exceptions.py
│   │   └── store.py             # InMemoryStore
│   ├── ingestion/
│   │   ├── document_loader.py
│   │   ├── ticket_loader.py
│   │   └── crew_loader.py
│   └── models/
│       ├── document.py
│       ├── ticket.py
│       ├── comment.py
│       ├── crew_member.py
│       └── enums.py
├── tests/
│   ├── conftest.py              # seeded_store fixture, client fixture
│   ├── test_documents.py
│   ├── test_tickets.py
│   ├── test_analytics.py
│   └── test_ai.py
├── crew.csv                     # seed crew data
├── documents.csv                # seed document data (also the RAG corpus)
├── tickets.csv                  # seed ticket data
├── .env.example
└── requirements.txt
```

## Getting Started

### Prerequisites

- Python 3.11 or later.
- [Ollama](https://ollama.com) installed separately — a native
  application, not a Python package.

### 1. Set up the virtual environment

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and set `API_KEY` to a value of your choosing, and confirm
the CSV paths, Ollama URL, and model names match your machine.

### 4. Pull the local models

With Ollama running:

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
ollama list        # confirm both models are present
```

### 5. Run the API

```bash
fastapi dev app/api/main.py
```

The API is now available at `http://127.0.0.1:8000`, with interactive
docs at `http://127.0.0.1:8000/docs`.

There's no separate vector-store build step. The first call to `/ask`
builds the Chroma collection automatically from `documents.csv` and
persists it — that first request will be noticeably slower (chunking
and embedding the whole corpus) than every request after it, which
just reopens the persisted store.

### Authentication

Every route except the root health check (`GET /`) requires an
`X-API-Key` header matching the `API_KEY` value in your `.env`. In
Swagger UI, click **Authorize** and enter the key once; from a script
or `curl`, pass it as a header on every request.

## API Reference

| Method | Path | Description |
|---|---|---|
| GET | `/` | Health check — no API key required |
| GET | `/documents` | Paginated list of documents |
| GET | `/documents/stale` | Documents overdue for review (excludes Incident Reports) |
| GET | `/documents/{document_id}` | A single document by id, including its full body |
| GET | `/tickets` | Paginated list of tickets |
| GET | `/tickets/mismatches` | Open tickets assigned to a different station than the one that owns the related document |
| GET | `/tickets/{ticket_id}` | A single ticket by id |
| GET | `/analytics/workload` | Per-station open-ticket load |
| GET | `/analytics/ownership` | Per-station document ownership & staleness (`?threshold=` optional) |
| POST | `/ask` | Grounded Q&A with citations and session memory |

A few behaviors worth knowing about, rather than discovering by
surprise:

- **"Open" means different things in different reports, on purpose.**
  `/analytics/workload` counts a ticket as open if its status is
  `Open` *or* `In-Progress`, since both represent active work a
  station is carrying. `/tickets/mismatches` only considers tickets
  that are strictly `Open`, since a mismatch already being worked on
  in-progress is a different (lower-urgency) situation than one that
  hasn't been picked up at all.
- **Empty stations don't appear in analytics reports.** A station
  with zero open tickets or zero owned documents is simply omitted
  from `/analytics/workload` or `/analytics/ownership`, rather than
  showing up with a `0`.
- **Crew data has no REST endpoint.** `crew.csv` exists purely to
  drive the analytics above (who owns which documents, who's assigned
  to which station) — there's no `/crew` route.

## Running Tests

```bash
pytest
```

40 tests total, covering:

- Analytics functions (`compute_station_workload`,
  `compute_document_ownership`, `find_station_mismatches`) called
  directly with hand-built data, independent of the API layer.
- `chunking.py`, `memory.py`, and the citation/context helpers in
  `chains.py` — pure unit tests, no Ollama required.
- Every router end-to-end via `TestClient` against a shared
  `seeded_store` fixture, including the `X-API-Key` requirement on
  each one.
- A small live-Ollama tier in `test_ai.py` that calls `ask_question()`
  against a real embedding + chat model. These three tests skip
  automatically (rather than failing) if Ollama isn't reachable, so
  the rest of the suite stays green without it running.

## Data

- `documents.csv` — Hearthline's knowledge base: recipes, SOPs,
  incident reports, and onboarding guides. This same file backs both
  the `/documents` REST endpoints and the retrieval corpus behind
  `/ask`.
- `tickets.csv` — operational tickets, referencing both
  `documents.csv` (via `related_document_id`) and `crew.csv` (via
  `assignee_id`).
- `crew.csv` — Hearthline's kitchen staff, each assigned to a station
  (Grill, Pastry, Prep, or Front of House).

All three are small, hand-authored seed datasets sized for
demonstrating the concepts clearly, not a realistic production
corpus.

## Project Status

LineMate was built in three phases — a read-only REST API, pandas/
numpy analytics, and retrieval-augmented Q&A — and is feature-complete
across all three. A fourth phase (an agentic layer using LangGraph and
MCP) was scoped early on but cut before implementation; this project
is complete without it.
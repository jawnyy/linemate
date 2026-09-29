import time

from fastapi import FastAPI, Request

from app.api.routers import documents, tickets  # , analytics, ask

app = FastAPI(title="LineMate", version="0.1.0")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    print(f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f}ms)")
    return response


@app.get("/")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "LineMate"}


app.include_router(documents.router)
app.include_router(tickets.router)
# app.include_router(analytics.router)
# app.include_router(ask.router)
from __future__ import annotations

from app.api.agent_routes import router as agent_router
from app.api.kb_routes import router as kb_router
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.api.routes import router as task_router
from app.core.exceptions import DomainError
from app.ui import render_index_page


app = FastAPI(
    title="Data Process PoC",
    version="0.1.0",
    description="AI-assisted data processing PoC with explicit workflow boundaries.",
)
app.include_router(task_router)
app.include_router(kb_router)
app.include_router(agent_router)


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return render_index_page()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(DomainError)
async def handle_domain_error(_: Request, error: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "code": error.code,
            "message": error.message,
            "data": {},
        },
    )

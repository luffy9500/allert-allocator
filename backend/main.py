"""
Entry point FastAPI.

In sviluppo locale:
    uvicorn backend.main:app --reload --port 8000
    (il frontend Vite gira su :5173 con proxy /api → :8000)

In produzione (Vercel):
    FastAPI serve sia le API sia i file statici del frontend React
    dalla directory frontend/dist costruita durante il deploy.
"""

import traceback

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .router_upload import router as upload_router
from .router_elabora import router as elabora_router
from .router_export import router as export_router

# Percorso assoluto della build React (prodotto da: cd frontend && npm run build)
_DIST = Path(__file__).parent.parent / "frontend" / "dist"

app = FastAPI(
    title="Allert Allocator",
    description="Motore di riallocazione prodotti in scadenza da CEDI verso PDV",
    version="1.0.0",
)

# CORS: necessario solo in sviluppo (frontend Vite su porta 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# Routers API
app.include_router(upload_router)
app.include_router(elabora_router)
app.include_router(export_router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Restituisce sempre JSON per le eccezioni non gestite (evita plain-text 500 da Vercel)."""
    return JSONResponse(
        status_code=500,
        content={"detail": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc()},
    )


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Serving del frontend React (solo se la build è presente)
# Deve stare DOPO i router /api altrimenti il catch-all intercetta le API.
# ---------------------------------------------------------------------------

if _DIST.exists():
    # Monta gli asset compilati (js/css/img) su /assets
    _assets = _DIST / "assets"
    if _assets.exists():
        app.mount("/assets", StaticFiles(directory=str(_assets)), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str) -> FileResponse:
        """
        Catch-all per il SPA React:
        - restituisce il file specifico se esiste in dist/
        - altrimenti restituisce index.html (React Router gestisce il routing)
        """
        requested = _DIST / full_path
        if requested.exists() and requested.is_file():
            return FileResponse(str(requested))
        return FileResponse(str(_DIST / "index.html"))

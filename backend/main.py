"""
Entry point FastAPI per il servizio di riallocazione prodotti in scadenza.

Avvio sviluppo:
    cd allert-allocator
    uvicorn backend.main:app --reload --port 8000

Il frontend React è servito in sviluppo da Vite (porta 5173) e configurato
per fare proxy delle chiamate /api verso questo server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .router_upload import router as upload_router
from .router_elabora import router as elabora_router
from .router_export import router as export_router

app = FastAPI(
    title="Allert Allocator",
    description="Motore di riallocazione prodotti in scadenza da CEDI verso PDV",
    version="1.0.0",
)

# CORS: in sviluppo accetta richieste dal frontend Vite (porta 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

app.include_router(upload_router)
app.include_router(elabora_router)
app.include_router(export_router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}

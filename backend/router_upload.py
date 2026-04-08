"""
Endpoint per l'upload dei file Excel.

Ogni file viene letto in memoria con pandas e salvato nella sessione utente.
Non vengono scritti file temporanei su disco.
"""

from __future__ import annotations

import io

import pandas as pd
from fastapi import APIRouter, Header, HTTPException, Request, UploadFile, File

from . import session_store
from .engine import (
    prepara_cedi,
    prepara_ceduto_7gg,
    prepara_ceduto_14gg,
    prepara_ceduto_30gg,
    prepara_ceduto_60gg,
    prepara_vendite_pdv,
    prepara_anagrafica,
    trasforma_ceduto_raw,
)
from .models import UploadResponse

router = APIRouter(prefix="/api/upload", tags=["upload"])

# Mappa tipo_file → (funzione di preparazione, nome attributo in SessionData)
_TIPO_CONFIG = {
    "cedi_scadenze":  (prepara_cedi,        "cedi"),
    "ceduto_7gg":     (prepara_ceduto_7gg,  "ceduto_7gg"),
    "ceduto_14gg":    (prepara_ceduto_14gg, "ceduto_14gg"),
    "ceduto_30gg":    (prepara_ceduto_30gg, "ceduto_30gg"),
    "ceduto_60gg":    (prepara_ceduto_60gg, "ceduto_60gg"),
    "vendite_pdv":    (prepara_vendite_pdv, "vendite"),
    "anagrafica_pdv": (prepara_anagrafica,  "anagrafica"),
}

# Periodo corrispondente a ogni tipo ceduto (per la trasformazione raw)
_CEDUTO_PERIODI = {
    "ceduto_7gg":  "7GG",
    "ceduto_14gg": "14GG",
    "ceduto_30gg": "30GG",
    "ceduto_60gg": "60GG",
}


@router.post("/{tipo_file}", response_model=UploadResponse)
async def upload_file(
    tipo_file: str,
    file: UploadFile = File(...),
    x_session_id: str = Header(..., alias="X-Session-ID"),
) -> UploadResponse:
    """
    Carica un file Excel per la sessione corrente.

    Per i file ceduto accetta sia il formato standard (colonne nominate)
    sia il formato grezzo (colonne posizionali, multi-foglio).
    Il formato grezzo viene rilevato automaticamente e trasformato.
    """
    if tipo_file not in _TIPO_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo file non valido: '{tipo_file}'. "
                   f"Valori ammessi: {sorted(_TIPO_CONFIG)}",
        )

    content = await file.read()
    prepara_fn, attr_name = _TIPO_CONFIG[tipo_file]

    if tipo_file in _CEDUTO_PERIODI:
        # ── File ceduto: prova prima il formato standard, poi il grezzo ──────
        periodo = _CEDUTO_PERIODI[tipo_file]
        try:
            df_raw = pd.read_excel(io.BytesIO(content))
            df_clean = prepara_fn(df_raw)
        except (ValueError, KeyError):
            # Formato standard non riconosciuto → prova trasformazione raw
            try:
                df_trasformato = trasforma_ceduto_raw(content, periodo)
                df_clean = prepara_fn(df_trasformato)
            except ValueError as exc:
                raise HTTPException(
                    status_code=422,
                    detail=f"Formato non riconosciuto ({periodo}): {exc}",
                )
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Impossibile leggere il file Excel: {exc}")
    else:
        # ── Altri file: flusso standard ───────────────────────────────────────
        try:
            df_raw = pd.read_excel(io.BytesIO(content))
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Impossibile leggere il file Excel: {exc}")
        try:
            df_clean = prepara_fn(df_raw)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

    # Salva nella sessione
    session = session_store.get_or_create(x_session_id)
    setattr(session, attr_name, df_clean)

    return UploadResponse(
        tipo=tipo_file,
        righe=len(df_clean),
        colonne=list(df_clean.columns),
        messaggio=f"File '{file.filename}' caricato: {len(df_clean)} righe.",
    )


class ChunkUploadResponse(UploadResponse):
    chunk_received: bool = False
    chunks_buffered: int = 0


@router.post("/json/{tipo_file}")
async def upload_json_data(
    tipo_file: str,
    request: Request,
    x_session_id: str = Header(..., alias="X-Session-ID"),
):
    """
    Carica dati ceduto pre-elaborati client-side come JSON.

    Body: {
      "righe": [...],
      "is_last_chunk": true   # opzionale, default true (upload singolo)
    }

    Per file grandi il frontend invia N chunk con is_last_chunk=false e poi
    l'ultimo con is_last_chunk=true, che trigghera l'elaborazione.
    """
    if tipo_file not in _TIPO_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo file non valido: '{tipo_file}'.",
        )

    body = await request.json()
    righe = body.get("righe", [])
    is_last_chunk = body.get("is_last_chunk", True)

    if not righe and is_last_chunk:
        raise HTTPException(status_code=422, detail="Payload vuoto: nessuna riga ricevuta.")

    session = session_store.get_or_create(x_session_id)

    # Accumula nel buffer della sessione
    if tipo_file not in session._chunk_buffers:
        session._chunk_buffers[tipo_file] = []
    session._chunk_buffers[tipo_file].extend(righe)

    if not is_last_chunk:
        # Chunk intermedio: conferma ricezione senza elaborare
        return {
            "tipo": tipo_file,
            "righe": 0,
            "colonne": [],
            "messaggio": f"Chunk ricevuto ({len(session._chunk_buffers[tipo_file])} righe in buffer).",
            "chunk_received": True,
            "chunks_buffered": len(session._chunk_buffers[tipo_file]),
        }

    # Ultimo chunk: elabora tutto il buffer
    tutte_le_righe = session._chunk_buffers.pop(tipo_file, [])
    if not tutte_le_righe:
        raise HTTPException(status_code=422, detail="Buffer vuoto: nessuna riga ricevuta.")

    df = pd.DataFrame(tutte_le_righe)
    prepara_fn, attr_name = _TIPO_CONFIG[tipo_file]

    try:
        df_clean = prepara_fn(df)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    setattr(session, attr_name, df_clean)

    return UploadResponse(
        tipo=tipo_file,
        righe=len(df_clean),
        colonne=list(df_clean.columns),
        messaggio=f"Elaborato nel browser: {len(df_clean)} righe.",
    )

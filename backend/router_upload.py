"""
Endpoint per l'upload dei file Excel.

Ogni file viene letto in memoria con pandas e salvato nella sessione utente.
Non vengono scritti file temporanei su disco.
"""

from __future__ import annotations

import io

import pandas as pd
from fastapi import APIRouter, Header, HTTPException, UploadFile, File

from . import session_store
from .engine import (
    prepara_cedi,
    prepara_ceduto_cedi,
    prepara_vendite_pdv,
    prepara_anagrafica,
)
from .models import UploadResponse

router = APIRouter(prefix="/api/upload", tags=["upload"])

# Mappa tipo_file → (funzione di preparazione, nome attributo in SessionData)
_TIPO_CONFIG = {
    "cedi_scadenze": (prepara_cedi, "cedi"),
    "ceduto_cedi": (prepara_ceduto_cedi, "ceduto"),
    "vendite_pdv": (prepara_vendite_pdv, "vendite"),
    "anagrafica_pdv": (prepara_anagrafica, "anagrafica"),
}


@router.post("/{tipo_file}", response_model=UploadResponse)
async def upload_file(
    tipo_file: str,
    file: UploadFile = File(...),
    x_session_id: str = Header(..., alias="X-Session-ID"),
) -> UploadResponse:
    """
    Carica un file Excel per la sessione corrente.

    tipo_file: cedi_scadenze | ceduto_cedi | vendite_pdv | anagrafica_pdv
    """
    if tipo_file not in _TIPO_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo file non valido: '{tipo_file}'. "
                   f"Valori ammessi: {sorted(_TIPO_CONFIG)}",
        )

    # Leggi il file Excel in memoria
    content = await file.read()
    try:
        df_raw = pd.read_excel(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Impossibile leggere il file Excel: {exc}")

    # Valida e normalizza secondo il tipo
    prepara_fn, attr_name = _TIPO_CONFIG[tipo_file]
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

"""
Storage in-memory dei DataFrame per sessione utente.

Ogni sessione è identificata da un UUID generato lato client e passato
nell'header X-Session-ID. I dati vivono per tutta la durata del processo
(nessuna persistenza su disco nell'MVP).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd


@dataclass
class SessionData:
    cedi: Optional[pd.DataFrame] = None
    # Ceduto CEDI suddiviso per finestra temporale (solo 7gg obbligatorio)
    ceduto_7gg:  Optional[pd.DataFrame] = None
    ceduto_14gg: Optional[pd.DataFrame] = None
    ceduto_30gg: Optional[pd.DataFrame] = None
    ceduto_60gg: Optional[pd.DataFrame] = None
    vendite: Optional[pd.DataFrame] = None
    anagrafica: Optional[pd.DataFrame] = None
    # Ultimo risultato elaborazione, mantenuto per l'export
    risultato_df: Optional[pd.DataFrame] = None
    risultato_summary: Optional[dict] = None
    risultato_avvisi: list[str] = field(default_factory=list)
    # Buffer temporaneo per upload a chunk: { tipo_file: [rows...] }
    _chunk_buffers: dict = field(default_factory=dict)


# Registro globale delle sessioni: { session_id: SessionData }
_sessions: dict[str, SessionData] = {}


def get_or_create(session_id: str) -> SessionData:
    """Restituisce la sessione esistente o ne crea una nuova."""
    if session_id not in _sessions:
        _sessions[session_id] = SessionData()
    return _sessions[session_id]


def get(session_id: str) -> Optional[SessionData]:
    """Restituisce la sessione se esiste, altrimenti None."""
    return _sessions.get(session_id)


def clear(session_id: str) -> None:
    """Elimina i dati di una sessione."""
    _sessions.pop(session_id, None)

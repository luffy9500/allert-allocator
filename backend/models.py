"""
Pydantic models per request / response delle API FastAPI.
"""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ElaboraRequest(BaseModel):
    modalita: Literal["ceduto", "venduto"] = Field(
        ..., description="Modalità di calcolo: 'ceduto' (CEDUTO_CEDI) o 'venduto' (VENDITE_PDV)"
    )


# ---------------------------------------------------------------------------
# Response models — upload
# ---------------------------------------------------------------------------

class UploadResponse(BaseModel):
    tipo: str
    righe: int
    colonne: list[str]
    messaggio: str


# ---------------------------------------------------------------------------
# Response models — elaborazione
# ---------------------------------------------------------------------------

class SummaryStats(BaseModel):
    totale_stock: float
    quantita_a_rischio: float
    referenze_critiche: int
    quantita_allocata: float
    quantita_non_allocata: float
    n_referenze: int
    n_pdv_coinvolti: int


class AllocazioneRow(BaseModel):
    lotto: str
    cod_articolo: str
    descrizione_articolo: str
    cod_pdv: str
    nome_pdv: str
    giorni_residui: int
    indice_rot: float
    capacita_stimata: float
    qta_proposta: int
    um: str                              # "colli" (ceduto) | "pezzi" (venduto)
    priorita: str
    motivo: str
    modalita_calcolo: str
    sconto_proposto: float | None = None  # es. 0.25 = 25%; None = nessuno sconto


class PDVAssignment(BaseModel):
    """Singola assegnazione PDV nell'ambito di una referenza completa."""
    lotto: str
    cod_pdv: str
    nome_pdv: str
    qta_proposta: int
    um: str
    indice_rot: float
    capacita_stimata: float
    motivo: str
    sconto_proposto: float | None = None


class ReferenzaCompletaRow(BaseModel):
    """Riepilogo per articolo con tutti i PDV assegnati. Incluso in ElaboraResponse
    per permettere al frontend di navigare senza ri-chiamare il server."""
    cod_articolo: str
    descrizione_articolo: str
    data_scadenza: str          # scadenza più urgente tra i lotti
    giorni_residui: int         # della scadenza più urgente
    qta_disponibile: float      # somma su tutti i lotti
    qta_allocata: float
    n_pdv_idonei: int
    priorita: str
    sconto_proposto: float | None = None
    lotti: list[str]
    pdv: list[PDVAssignment]


class ElaboraResponse(BaseModel):
    summary: SummaryStats
    allocazioni: list[AllocazioneRow]
    avvisi: list[str]
    referenze: list[ReferenzaCompletaRow] = []


# ---------------------------------------------------------------------------
# Response models — referenze (Elenco Referenze page)
# ---------------------------------------------------------------------------

class ReferenzaRow(BaseModel):
    cod_articolo: str
    descrizione_articolo: str
    data_scadenza: str          # ISO format YYYY-MM-DD
    giorni_residui: int
    qta_disponibile: float
    n_pdv_idonei: int
    priorita: str


class ElencoReferenzeResponse(BaseModel):
    referenze: list[ReferenzaRow]


# ---------------------------------------------------------------------------
# Response models — dettaglio singola referenza
# ---------------------------------------------------------------------------

class DettaglioPDVRow(BaseModel):
    cod_pdv: str
    nome_pdv: str
    indice_rot: float
    capacita_stimata: float
    qta_proposta: int
    motivo: str


class DettaglioReferenzaResponse(BaseModel):
    cod_articolo: str
    descrizione_articolo: str
    giorni_residui: int
    qta_disponibile: float
    priorita: str
    pdv: list[DettaglioPDVRow]


# ---------------------------------------------------------------------------
# Response generica per errori
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    detail: str

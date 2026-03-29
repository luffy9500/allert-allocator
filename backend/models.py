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
    priorita: str
    motivo: str
    modalita_calcolo: str


class ElaboraResponse(BaseModel):
    summary: SummaryStats
    allocazioni: list[AllocazioneRow]
    avvisi: list[str]


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

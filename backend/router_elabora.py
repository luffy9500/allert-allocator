"""
Endpoint per l'elaborazione del piano di riallocazione e per la
consultazione dei risultati (dashboard, referenze, dettaglio).
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Header, HTTPException

from . import session_store
from .engine import elabora_riallocazione, assegna_priorita, unisci_ceduto
from .models import (
    ElaboraRequest,
    ElaboraResponse,
    SummaryStats,
    AllocazioneRow,
    ElencoReferenzeResponse,
    ReferenzaRow,
    DettaglioReferenzaResponse,
    DettaglioPDVRow,
)

router = APIRouter(prefix="/api", tags=["elabora"])


def _require_session(session_id: str) -> session_store.SessionData:
    """Restituisce la sessione oppure lancia 404."""
    sess = session_store.get(session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="Sessione non trovata. Ricaricare i file.")
    return sess


# ---------------------------------------------------------------------------
# POST /api/elabora
# ---------------------------------------------------------------------------

@router.post("/elabora", response_model=ElaboraResponse)
def elabora(
    body: ElaboraRequest,
    x_session_id: str = Header(..., alias="X-Session-ID"),
) -> ElaboraResponse:
    """
    Esegue il calcolo di riallocazione per la sessione corrente.

    Richiede almeno CEDI_SCADENZE + il file corrispondente alla modalità scelta:
      - modalita "ceduto" → richiede CEDUTO_CEDI
      - modalita "venduto" → richiede VENDITE_PDV
    """
    sess = _require_session(x_session_id)

    if sess.cedi is None:
        raise HTTPException(status_code=422, detail="File CEDI_SCADENZE non caricato.")

    if body.modalita == "ceduto" and sess.ceduto_7gg is None:
        raise HTTPException(status_code=422, detail="Modalità 'ceduto' richiede almeno il file CEDUTO_7GG.")

    if body.modalita == "venduto" and sess.vendite is None:
        raise HTTPException(status_code=422, detail="Modalità 'venduto' richiede il file VENDITE_PDV.")

    if body.modalita == "ceduto":
        rotazione_df = unisci_ceduto(
            sess.ceduto_7gg, sess.ceduto_14gg, sess.ceduto_30gg, sess.ceduto_60gg
        )
    else:
        rotazione_df = sess.vendite

    risultato = elabora_riallocazione(
        cedi_df=sess.cedi,
        rotazione_df=rotazione_df,
        anagrafica_df=sess.anagrafica,
        modalita=body.modalita,
    )

    # Persiste il risultato nella sessione per export successivo
    sess.risultato_df = risultato["allocazioni"]
    sess.risultato_summary = risultato["summary"]
    sess.risultato_avvisi = risultato["avvisi"]

    # Costruisce la response
    s = risultato["summary"]
    allocazioni = [
        AllocazioneRow(
            lotto=str(row["LOTTO"]),
            cod_articolo=str(row["COD_ARTICOLO"]),
            descrizione_articolo=str(row["DESCRIZIONE_ARTICOLO"]),
            cod_pdv=str(row["COD_PDV"]),
            nome_pdv=str(row["NOME_PDV"]),
            giorni_residui=int(row["GIORNI_RESIDUI"]),
            indice_rot=float(row["INDICE_ROT"]),
            capacita_stimata=float(row["CAPACITA_STIMATA"]),
            qta_proposta=int(row["QTA_PROPOSTA"]),
            um=str(row["UM"]),
            priorita=str(row["PRIORITA"]),
            motivo=str(row["MOTIVO"]),
            modalita_calcolo=str(row["MODALITA_CALCOLO"]),
            sconto_proposto=float(row["SCONTO_PROPOSTO"]) if row["SCONTO_PROPOSTO"] is not None else None,
        )
        for _, row in risultato["allocazioni"].iterrows()
    ]

    return ElaboraResponse(
        summary=SummaryStats(**s),
        allocazioni=allocazioni,
        avvisi=risultato["avvisi"],
    )


# ---------------------------------------------------------------------------
# GET /api/referenze  — elenco articoli con riepilogo
# ---------------------------------------------------------------------------

@router.get("/referenze", response_model=ElencoReferenzeResponse)
def elenco_referenze(
    x_session_id: str = Header(..., alias="X-Session-ID"),
) -> ElencoReferenzeResponse:
    """
    Restituisce l'elenco delle referenze in scadenza con statistiche sintetiche.
    Richiede che /elabora sia già stato chiamato.
    """
    sess = _require_session(x_session_id)

    if sess.cedi is None:
        raise HTTPException(status_code=422, detail="File CEDI_SCADENZE non caricato.")

    oggi = date.today()
    righe: list[ReferenzaRow] = []

    for _, row in sess.cedi.iterrows():
        cod = str(row["COD_ARTICOLO"])
        giorni = (row["DATA_SCADENZA"].date() - oggi).days

        # Conta PDV idonei se il risultato è disponibile
        n_pdv = 0
        if sess.risultato_df is not None and not sess.risultato_df.empty:
            n_pdv = int(
                sess.risultato_df[sess.risultato_df["COD_ARTICOLO"] == cod]["COD_PDV"].nunique()
            )

        righe.append(ReferenzaRow(
            cod_articolo=cod,
            descrizione_articolo=str(row["DESCRIZIONE_ARTICOLO"]),
            data_scadenza=row["DATA_SCADENZA"].date().isoformat(),
            giorni_residui=giorni,
            qta_disponibile=float(row["QTA_DISPONIBILE_COLLI"]),
            n_pdv_idonei=n_pdv,
            priorita=assegna_priorita(giorni),
        ))

    # Ordina per giorni residui crescenti
    righe.sort(key=lambda r: r.giorni_residui)

    return ElencoReferenzeResponse(referenze=righe)


# ---------------------------------------------------------------------------
# GET /api/referenze/{cod_articolo}  — dettaglio singola referenza
# ---------------------------------------------------------------------------

@router.get("/referenze/{cod_articolo}", response_model=DettaglioReferenzaResponse)
def dettaglio_referenza(
    cod_articolo: str,
    x_session_id: str = Header(..., alias="X-Session-ID"),
) -> DettaglioReferenzaResponse:
    """
    Restituisce il dettaglio di una referenza con il ranking PDV e le quantità proposte.
    Richiede che /elabora sia già stato chiamato.
    """
    sess = _require_session(x_session_id)

    if sess.cedi is None:
        raise HTTPException(status_code=422, detail="File CEDI_SCADENZE non caricato.")

    # Cerca la referenza nel CEDI
    cedi_row = sess.cedi[sess.cedi["COD_ARTICOLO"] == cod_articolo]
    if cedi_row.empty:
        raise HTTPException(status_code=404, detail=f"Referenza '{cod_articolo}' non trovata.")

    row = cedi_row.iloc[0]
    giorni = (row["DATA_SCADENZA"].date() - date.today()).days

    pdv_list: list[DettaglioPDVRow] = []
    if sess.risultato_df is not None and not sess.risultato_df.empty:
        subset = sess.risultato_df[sess.risultato_df["COD_ARTICOLO"] == cod_articolo]
        for _, pr in subset.iterrows():
            pdv_list.append(DettaglioPDVRow(
                cod_pdv=str(pr["COD_PDV"]),
                nome_pdv=str(pr["NOME_PDV"]),
                indice_rot=float(pr["INDICE_ROT"]),
                capacita_stimata=float(pr["CAPACITA_STIMATA"]),
                qta_proposta=int(pr["QTA_PROPOSTA"]),
                motivo=str(pr["MOTIVO"]),
            ))

    return DettaglioReferenzaResponse(
        cod_articolo=cod_articolo,
        descrizione_articolo=str(row["DESCRIZIONE_ARTICOLO"]),
        giorni_residui=giorni,
        qta_disponibile=float(row["QTA_DISPONIBILE_COLLI"]),
        priorita=assegna_priorita(giorni),
        pdv=pdv_list,
    )

"""
Motore di calcolo per la riallocazione di prodotti in scadenza.
Supporta due modalità:
  - "ceduto": basata su dati di ceduto CEDI (7/14/30gg), coeff 0.7
  - "venduto": basata su vendite mensili PDV,             coeff 0.8
"""

from __future__ import annotations

import math
from datetime import date
from typing import Literal

import pandas as pd


# ---------------------------------------------------------------------------
# Costanti
# ---------------------------------------------------------------------------

MODALITA_CEDUTO = "ceduto"
MODALITA_VENDUTO = "venduto"

COEFF_CEDUTO = 0.7
COEFF_VENDUTO = 0.8

SOGLIA_INDICE_MIN = 0.2          # PDV con indice inferiore vengono esclusi
MAX_PDV_NORMALE = 10
MAX_PDV_CRITICO = 3              # usato quando GIORNI_RESIDUI <= 2
GIORNI_CRITICI = 2
SOGLIA_PRIORITA_ALTA = 5
SOGLIA_PRIORITA_MEDIA = 15


# ---------------------------------------------------------------------------
# Validazione / caricamento DataFrame
# ---------------------------------------------------------------------------

def valida_colonne(df: pd.DataFrame, required: set[str], nome: str) -> None:
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{nome}: colonne mancanti: {sorted(missing)}")


def prepara_cedi(df: pd.DataFrame) -> pd.DataFrame:
    """Valida e normalizza il DataFrame CEDI_SCADENZE."""
    valida_colonne(
        df,
        {"LOTTO", "COD_ARTICOLO", "DESCRIZIONE_ARTICOLO", "QTA_DISPONIBILE", "DATA_SCADENZA"},
        "CEDI_SCADENZE",
    )
    df = df.copy()
    df["DATA_SCADENZA"] = pd.to_datetime(df["DATA_SCADENZA"])
    df["QTA_DISPONIBILE"] = pd.to_numeric(df["QTA_DISPONIBILE"], errors="raise")
    return df


def prepara_ceduto_7gg(df: pd.DataFrame) -> pd.DataFrame:
    """Valida e normalizza il file ceduto CEDI — finestra 7 giorni."""
    valida_colonne(df, {"COD_PDV", "NOME_PDV", "COD_ARTICOLO", "QTA_CEDUTA_7GG"}, "CEDUTO_7GG")
    df = df.copy()
    df["QTA_CEDUTA_7GG"] = pd.to_numeric(df["QTA_CEDUTA_7GG"], errors="raise").fillna(0)
    return df[["COD_PDV", "NOME_PDV", "COD_ARTICOLO", "QTA_CEDUTA_7GG"]]


def prepara_ceduto_14gg(df: pd.DataFrame) -> pd.DataFrame:
    """Valida e normalizza il file ceduto CEDI — finestra 14 giorni."""
    valida_colonne(df, {"COD_PDV", "NOME_PDV", "COD_ARTICOLO", "QTA_CEDUTA_14GG"}, "CEDUTO_14GG")
    df = df.copy()
    df["QTA_CEDUTA_14GG"] = pd.to_numeric(df["QTA_CEDUTA_14GG"], errors="raise").fillna(0)
    return df[["COD_PDV", "NOME_PDV", "COD_ARTICOLO", "QTA_CEDUTA_14GG"]]


def prepara_ceduto_30gg(df: pd.DataFrame) -> pd.DataFrame:
    """Valida e normalizza il file ceduto CEDI — finestra 30 giorni."""
    valida_colonne(df, {"COD_PDV", "NOME_PDV", "COD_ARTICOLO", "QTA_CEDUTA_30GG"}, "CEDUTO_30GG")
    df = df.copy()
    df["QTA_CEDUTA_30GG"] = pd.to_numeric(df["QTA_CEDUTA_30GG"], errors="raise").fillna(0)
    return df[["COD_PDV", "NOME_PDV", "COD_ARTICOLO", "QTA_CEDUTA_30GG"]]


def unisci_ceduto(
    df_7: pd.DataFrame,
    df_14: pd.DataFrame | None,
    df_30: pd.DataFrame | None,
) -> pd.DataFrame:
    """
    Fonde i tre DataFrame ceduto in uno unico compatibile con calcola_indice_ceduto().

    - df_7  è obbligatorio (finestra più recente, peso 50%)
    - df_14 e df_30 sono opzionali: se assenti le rispettive QTA valgono 0
      (il calcolo degrada gracefully usando solo i dati disponibili)

    Il join è left su df_7 → ogni PDV/articolo presente nel file 7gg
    viene arricchito con i dati 14gg e 30gg se disponibili.
    """
    _CHIAVI = ["COD_PDV", "NOME_PDV", "COD_ARTICOLO"]
    df = df_7.copy()

    if df_14 is not None and not df_14.empty:
        df = df.merge(df_14[_CHIAVI + ["QTA_CEDUTA_14GG"]], on=_CHIAVI, how="left")
    else:
        df["QTA_CEDUTA_14GG"] = 0.0

    if df_30 is not None and not df_30.empty:
        df = df.merge(df_30[_CHIAVI + ["QTA_CEDUTA_30GG"]], on=_CHIAVI, how="left")
    else:
        df["QTA_CEDUTA_30GG"] = 0.0

    # Colma i NaN prodotti dal left-join con 0
    df[["QTA_CEDUTA_7GG", "QTA_CEDUTA_14GG", "QTA_CEDUTA_30GG"]] = (
        df[["QTA_CEDUTA_7GG", "QTA_CEDUTA_14GG", "QTA_CEDUTA_30GG"]].fillna(0)
    )
    return df


def prepara_vendite_pdv(df: pd.DataFrame) -> pd.DataFrame:
    """Valida e normalizza il DataFrame VENDITE_PDV."""
    valida_colonne(
        df,
        {"COD_PDV", "NOME_PDV", "COD_ARTICOLO", "QTA_VENDUTA_MESE"},
        "VENDITE_PDV",
    )
    df = df.copy()
    df["QTA_VENDUTA_MESE"] = pd.to_numeric(df["QTA_VENDUTA_MESE"], errors="raise").fillna(0)
    return df


def prepara_anagrafica(df: pd.DataFrame) -> pd.DataFrame:
    """Valida e normalizza il DataFrame ANAGRAFICA_PDV."""
    valida_colonne(
        df,
        {"COD_PDV", "ATTIVO"},
        "ANAGRAFICA_PDV",
    )
    df = df.copy()
    # Normalizza ATTIVO a bool (accetta True/False, 1/0, "si"/"no", "true"/"false")
    _truthy = {"true", "1", "si", "yes", "s", "y"}
    # Converte sempre a stringa per gestire uniformemente object, StringDtype e bool
    df["ATTIVO"] = df["ATTIVO"].astype(str).str.strip().str.lower().isin(_truthy)
    return df


# ---------------------------------------------------------------------------
# Calcolo indice di rotazione
# ---------------------------------------------------------------------------

def calcola_indice_ceduto(df: pd.DataFrame) -> pd.DataFrame:
    """
    INDICE_ROT = (QTA_CEDUTA_7GG/7 × 0.5) + (QTA_CEDUTA_14GG/14 × 0.3) + (QTA_CEDUTA_30GG/30 × 0.2)
    """
    df = df.copy()
    df["INDICE_ROT"] = (
        (df["QTA_CEDUTA_7GG"] / 7) * 0.5
        + (df["QTA_CEDUTA_14GG"] / 14) * 0.3
        + (df["QTA_CEDUTA_30GG"] / 30) * 0.2
    )
    return df


def calcola_indice_venduto(df: pd.DataFrame) -> pd.DataFrame:
    """
    INDICE_ROT = QTA_VENDUTA_MESE / 30
    """
    df = df.copy()
    df["INDICE_ROT"] = df["QTA_VENDUTA_MESE"] / 30
    return df


# ---------------------------------------------------------------------------
# Capacità stimata
# ---------------------------------------------------------------------------

def calcola_capacita(df: pd.DataFrame, giorni_residui: int, coeff: float) -> pd.DataFrame:
    """
    CAPACITA_STIMATA = INDICE_ROT × GIORNI_RESIDUI × coeff
    """
    df = df.copy()
    df["CAPACITA_STIMATA"] = df["INDICE_ROT"] * giorni_residui * coeff
    return df


# ---------------------------------------------------------------------------
# Filtro PDV
# ---------------------------------------------------------------------------

def filtra_pdv(pdv_df: pd.DataFrame, anagrafica_df: pd.DataFrame | None) -> pd.DataFrame:
    """
    Esclude PDV:
      - con INDICE_ROT == 0 o < SOGLIA_INDICE_MIN
      - non attivi (se anagrafica disponibile)
    """
    df = pdv_df.copy()

    # Filtro per attività da anagrafica
    if anagrafica_df is not None and not anagrafica_df.empty:
        attivi = anagrafica_df.loc[anagrafica_df["ATTIVO"], "COD_PDV"]
        df = df[df["COD_PDV"].isin(attivi)]

    # Filtro per indice minimo
    df = df[df["INDICE_ROT"] >= SOGLIA_INDICE_MIN]

    return df


# ---------------------------------------------------------------------------
# Priorità e motivo
# ---------------------------------------------------------------------------

def assegna_priorita(giorni_residui: int) -> str:
    if giorni_residui <= SOGLIA_PRIORITA_ALTA:
        return "Alta"
    if giorni_residui <= SOGLIA_PRIORITA_MEDIA:
        return "Media"
    return "Bassa"


def assegna_motivo(indice_rot: float, capacita_stimata: float, giorni_residui: int) -> str:
    if giorni_residui <= GIORNI_CRITICI:
        return "Prodotto critico"
    if indice_rot >= 1.5:
        return "Alta rotazione"
    if capacita_stimata < 5:
        return "Bassa capacità"
    return "Rotazione standard"


# ---------------------------------------------------------------------------
# Allocazione greedy con vincoli
# ---------------------------------------------------------------------------

def alloca_quantita(
    qta_disponibile: float,
    pdv_df: pd.DataFrame,
    giorni_residui: int,
) -> tuple[pd.DataFrame, float]:
    """
    Distribuisce qta_disponibile ai PDV in ordine di CAPACITA_STIMATA decrescente.

    Vincoli:
      - massimo MAX_PDV_CRITICO PDV se giorni_residui <= GIORNI_CRITICI
      - massimo MAX_PDV_NORMALE PDV altrimenti
      - non assegnare QTA_PROPOSTA < 1

    Returns:
        (df_allocato, quantita_non_allocata)
    """
    max_pdv = MAX_PDV_CRITICO if giorni_residui <= GIORNI_CRITICI else MAX_PDV_NORMALE

    # Ordina per capacità decrescente, poi per indice decrescente
    pdv_sorted = pdv_df.sort_values(
        ["CAPACITA_STIMATA", "INDICE_ROT"], ascending=[False, False]
    ).head(max_pdv).copy()

    pdv_sorted["QTA_PROPOSTA"] = 0.0
    rimanente = qta_disponibile

    for idx in pdv_sorted.index:
        if rimanente <= 0:
            break
        capacita = pdv_sorted.at[idx, "CAPACITA_STIMATA"]
        assegnato = min(capacita, rimanente)
        if assegnato < 1:
            continue
        # Arrotonda al numero intero inferiore per evitare frazioni non gestibili
        assegnato = math.floor(assegnato)
        pdv_sorted.at[idx, "QTA_PROPOSTA"] = assegnato
        rimanente -= assegnato

    allocato = pdv_sorted[pdv_sorted["QTA_PROPOSTA"] >= 1]
    quantita_non_allocata = max(0.0, rimanente)
    return allocato, quantita_non_allocata


# ---------------------------------------------------------------------------
# Orchestrazione principale
# ---------------------------------------------------------------------------

def elabora_riallocazione(
    cedi_df: pd.DataFrame,
    rotazione_df: pd.DataFrame,
    anagrafica_df: pd.DataFrame | None,
    modalita: Literal["ceduto", "venduto"],
    data_riferimento: date | None = None,
) -> dict:
    """
    Esegue il calcolo completo di riallocazione.

    Args:
        cedi_df:         DataFrame CEDI_SCADENZE già validato
        rotazione_df:    DataFrame CEDUTO_CEDI_PDV o VENDITE_PDV già validato
        anagrafica_df:   DataFrame ANAGRAFICA_PDV (opzionale)
        modalita:        "ceduto" oppure "venduto"
        data_riferimento: data odierna (default: date.today())

    Returns:
        {
            "allocazioni": pd.DataFrame,
            "summary":     dict,
            "avvisi":      list[str],
        }
    """
    if data_riferimento is None:
        data_riferimento = date.today()

    # Scegli la funzione di calcolo e il coefficiente in base alla modalità
    if modalita == MODALITA_CEDUTO:
        rotazione_df = calcola_indice_ceduto(rotazione_df)
        coeff = COEFF_CEDUTO
    else:
        rotazione_df = calcola_indice_venduto(rotazione_df)
        coeff = COEFF_VENDUTO

    righe_output: list[dict] = []
    avvisi: list[str] = []

    for _, lotto_row in cedi_df.iterrows():
        lotto = lotto_row["LOTTO"]
        cod_articolo = lotto_row["COD_ARTICOLO"]
        descrizione = lotto_row["DESCRIZIONE_ARTICOLO"]
        qta_disponibile = float(lotto_row["QTA_DISPONIBILE"])
        data_scadenza = lotto_row["DATA_SCADENZA"].date()

        giorni_residui = (data_scadenza - data_riferimento).days

        if giorni_residui <= 0:
            avvisi.append(f"Lotto {lotto} ({cod_articolo}): già scaduto il {data_scadenza} — saltato")
            continue

        # Filtra il DataFrame di rotazione per questo articolo
        pdv_articolo = rotazione_df[rotazione_df["COD_ARTICOLO"] == cod_articolo].copy()

        if pdv_articolo.empty:
            avvisi.append(f"Lotto {lotto} ({cod_articolo}): nessun PDV con storico — saltato")
            continue

        # Calcola capacità stimata
        pdv_articolo = calcola_capacita(pdv_articolo, giorni_residui, coeff)

        # Applica filtri PDV
        pdv_articolo = filtra_pdv(pdv_articolo, anagrafica_df)

        if pdv_articolo.empty:
            avvisi.append(f"Lotto {lotto} ({cod_articolo}): nessun PDV idoneo dopo i filtri")
            continue

        # Alloca la quantità disponibile
        allocazioni, qta_non_allocata = alloca_quantita(qta_disponibile, pdv_articolo, giorni_residui)

        if qta_non_allocata > 0:
            avvisi.append(
                f"Lotto {lotto} ({cod_articolo}): quantità non allocata = {qta_non_allocata:.0f} unità"
            )

        priorita = assegna_priorita(giorni_residui)

        for _, pdv_row in allocazioni.iterrows():
            indice = round(float(pdv_row["INDICE_ROT"]), 4)
            capacita = round(float(pdv_row["CAPACITA_STIMATA"]), 2)
            righe_output.append({
                "LOTTO": lotto,
                "COD_ARTICOLO": cod_articolo,
                "DESCRIZIONE_ARTICOLO": descrizione,
                "COD_PDV": pdv_row["COD_PDV"],
                "NOME_PDV": pdv_row["NOME_PDV"],
                "GIORNI_RESIDUI": giorni_residui,
                "INDICE_ROT": indice,
                "CAPACITA_STIMATA": capacita,
                "QTA_PROPOSTA": int(pdv_row["QTA_PROPOSTA"]),
                "PRIORITA": priorita,
                "MOTIVO": assegna_motivo(indice, capacita, giorni_residui),
                "MODALITA_CALCOLO": "Ceduto" if modalita == MODALITA_CEDUTO else "Venduto",
            })

    if not righe_output:
        output_df = pd.DataFrame(columns=[
            "LOTTO", "COD_ARTICOLO", "DESCRIZIONE_ARTICOLO", "COD_PDV", "NOME_PDV",
            "GIORNI_RESIDUI", "INDICE_ROT", "CAPACITA_STIMATA", "QTA_PROPOSTA",
            "PRIORITA", "MOTIVO", "MODALITA_CALCOLO",
        ])
    else:
        output_df = pd.DataFrame(righe_output)

        # Ordinamento finale: Alta → Media → Bassa, poi capacità decrescente
        priorita_order = {"Alta": 0, "Media": 1, "Bassa": 2}
        output_df["_pord"] = output_df["PRIORITA"].map(priorita_order)
        output_df = (
            output_df.sort_values(["_pord", "CAPACITA_STIMATA"], ascending=[True, False])
            .drop(columns=["_pord"])
            .reset_index(drop=True)
        )

    # Calcola summary
    summary = _calcola_summary(cedi_df, output_df, data_riferimento)

    return {
        "allocazioni": output_df,
        "summary": summary,
        "avvisi": avvisi,
    }


def _calcola_summary(
    cedi_df: pd.DataFrame,
    output_df: pd.DataFrame,
    data_riferimento: date,
) -> dict:
    """Calcola le statistiche di riepilogo per la Dashboard."""
    cedi = cedi_df.copy()
    cedi["GIORNI_RESIDUI"] = (
        pd.to_datetime(cedi["DATA_SCADENZA"]).dt.date.apply(
            lambda d: (d - data_riferimento).days
        )
    )

    totale_stock = float(cedi["QTA_DISPONIBILE"].sum())
    quantita_a_rischio = float(
        cedi.loc[cedi["GIORNI_RESIDUI"] <= SOGLIA_PRIORITA_ALTA, "QTA_DISPONIBILE"].sum()
    )
    referenze_critiche = int(
        cedi.loc[cedi["GIORNI_RESIDUI"] <= GIORNI_CRITICI, "COD_ARTICOLO"].nunique()
    )
    quantita_allocata = float(output_df["QTA_PROPOSTA"].sum()) if not output_df.empty else 0.0
    quantita_non_allocata = totale_stock - quantita_allocata
    n_referenze = int(cedi["COD_ARTICOLO"].nunique())
    n_pdv_coinvolti = int(output_df["COD_PDV"].nunique()) if not output_df.empty else 0

    return {
        "totale_stock": totale_stock,
        "quantita_a_rischio": quantita_a_rischio,
        "referenze_critiche": referenze_critiche,
        "quantita_allocata": quantita_allocata,
        "quantita_non_allocata": max(0.0, quantita_non_allocata),
        "n_referenze": n_referenze,
        "n_pdv_coinvolti": n_pdv_coinvolti,
    }

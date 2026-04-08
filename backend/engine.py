"""
Motore di calcolo per la riallocazione di prodotti in scadenza.
Supporta due modalità:
  - "ceduto": basata su dati di ceduto CEDI (7/14/30/60gg), unità colli, coeff 0.7
  - "venduto": basata su vendite mensili PDV,               unità pezzi, coeff 0.8
"""

from __future__ import annotations

import io
import math
import re
from collections import defaultdict
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
MAX_PDV_CRITICO = 3              # usato quando GIORNI_RESIDUI <= GIORNI_CRITICI
GIORNI_CRITICI = 2
SOGLIA_PRIORITA_ALTA = 5
SOGLIA_PRIORITA_MEDIA = 15


# ---------------------------------------------------------------------------
# Trasformazione file ceduto dal formato grezzo (colonne posizionali)
# ---------------------------------------------------------------------------

def rileva_periodo_ceduto(filename: str) -> str:
    """Rileva il periodo (7GG, 14GG, 30GG, 60GG) dal nome del file.

    Esempi:
        CEDUTO_MAG_20_7_GG.XLS  → "7GG"
        CEDUTO 14GG.XLS         → "14GG"
        file_senza_periodo.xls  → "7GG"  (default)
    """
    match = re.search(r'(\d+)\s*[-_]?\s*GG', filename, re.IGNORECASE)
    if match:
        try:
            n = int(match.group(1))
            if n in (7, 14, 30, 60):
                return f"{n}GG"
        except ValueError:
            pass
    return "7GG"


def trasforma_ceduto_raw(content: bytes, periodo: str) -> pd.DataFrame:
    """Legge un file ceduto dal formato grezzo (multi-foglio, colonne posizionali)
    e lo restituisce come DataFrame con le colonne standard attese da prepara_ceduto_Xgg.

    Layout colonne (indice 0-based, dopo aver saltato la riga header):
        col  9 → Radice articolo
        col 10 → Variante articolo
        col 12 → Tipo movimento  (tieni solo "L")
        col 14 → Pezzi
        col 15 → Imballo (0 o vuoto → usa 1)
        col 17 → Codice PDV
        col 18 → Nome PDV

    Trasformazioni:
        COD_ARTICOLO  = str(int(radice)) + str(int(variante)).zfill(2)
        QTA_COLLI     = round(pezzi / imballo)
        COD_PDV       = se 6 cifre e termina con "0" → rimuovi l'ultimo "0"
    """
    # ── Leggi tutti i fogli, senza interpretare header ───────────────────────
    try:
        all_sheets: dict[str, pd.DataFrame] = pd.read_excel(
            io.BytesIO(content),
            header=None,
            sheet_name=None,
            dtype=object,
        )
    except Exception as exc:
        raise ValueError(f"Impossibile leggere il file Excel: {exc}") from exc

    if not all_sheets:
        raise ValueError("File vuoto: nessun foglio trovato.")

    # ── Concatena i fogli saltando la riga 0 (header) di ognuno ──────────────
    frames: list[pd.DataFrame] = []
    for df_sheet in all_sheets.values():
        if df_sheet.empty:
            continue
        frames.append(df_sheet.iloc[1:].copy())

    if not frames:
        raise ValueError("Nessun dato dopo aver saltato le intestazioni.")

    df = pd.concat(frames, ignore_index=True)

    if df.shape[1] <= 17:
        raise ValueError(
            f"Il file ha solo {df.shape[1]} colonne; "
            "il formato grezzo ne richiede almeno 18 (indici 0–17)."
        )

    # ── Helper interni ────────────────────────────────────────────────────────
    def _to_int_str(val: object) -> str:
        """Converte un valore a stringa intera (30264.0 → '30264')."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ""
        try:
            return str(int(float(str(val).strip())))
        except (ValueError, TypeError):
            return str(val).strip()

    def _is_numeric(val: object) -> bool:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return False
        try:
            float(str(val).strip())
            return True
        except (ValueError, TypeError):
            return False

    # ── Step 2: Filtro righe valide ───────────────────────────────────────────
    # Colonne 1-based → indice 0-based: col9→8, col10→9, col12→11, col14→13,
    #                                   col15→14, col17→16, col18→17
    # Col 9 (1-based) = indice 8 = AM1CART = Radice
    mask_radice = df.iloc[:, 8].apply(_is_numeric)
    df = df[mask_radice].copy()

    if df.empty:
        raise ValueError(
            "Nessuna riga valida: colonna 9 (Radice, indice 8) sempre vuota o non numerica. "
            "Verificare che il file sia nel formato grezzo corretto."
        )

    # Col 12 (1-based) = indice 11 = AM1CLST = TipoMov — tieni solo "L"
    col11 = df.iloc[:, 11].astype(str).str.strip().str.upper()
    df = df[col11 == "L"].copy()

    if df.empty:
        raise ValueError(
            "Nessuna riga con tipo movimento = 'L' (colonna 12, indice 11). "
            "Verificare il formato del file."
        )

    # ── Step 3: Trasformazioni ────────────────────────────────────────────────
    # Col 14 (1-based) = indice 13 = AM1QESK01 = Pezzi
    # Col 15 (1-based) = indice 14 = ANQICV = Imballo
    pezzi   = pd.to_numeric(df.iloc[:, 13], errors="coerce").fillna(0)
    imballo = pd.to_numeric(df.iloc[:, 14], errors="coerce").fillna(0)
    imballo = imballo.replace(0, 1)  # imballo=0 o vuoto → usa 1

    colli = (pezzi / imballo).round().astype(int)

    # Scarta valori negativi
    mask_pos = (pezzi >= 0) & (colli >= 0)

    # COD_ARTICOLO: Col 9 (idx 8) = Radice + Col 10 (idx 9) = Variante zero-pad 2 cifre
    radice   = df.iloc[:, 8].apply(_to_int_str)
    variante = df.iloc[:, 9].apply(lambda v: _to_int_str(v).zfill(2) if _to_int_str(v) else "00")
    cod_articolo = radice + variante

    # COD_PDV: Col 17 (idx 16) = AM1CDST — 6 cifre con "0" finale → rimuovi lo zero
    def _normalizza_pdv(val: object) -> str:
        s = _to_int_str(val)
        if len(s) == 6 and s.endswith("0"):
            return s[:-1]
        return s

    # Col 17 (1-based) = indice 16 = AM1CDST = CodPDV
    # Col 18 (1-based) = indice 17 = NDXDST  = NomePDV
    cod_pdv  = df.iloc[:, 16].apply(_normalizza_pdv)
    nome_pdv = df.iloc[:, 17].astype(str).str.strip()

    # ── Step 4: Costruzione output ────────────────────────────────────────────
    col_colli = f"QTA_CEDUTA_{periodo}_COLLI"
    col_pezzi = f"QTA_CEDUTA_{periodo}_PEZZI"

    result = pd.DataFrame({
        "COD_PDV":      cod_pdv,
        "NOME_PDV":     nome_pdv,
        "COD_ARTICOLO": cod_articolo,
        col_colli:      colli,
        col_pezzi:      pezzi.round().astype(int),
    })

    result = result[mask_pos.values].reset_index(drop=True)

    if result.empty:
        raise ValueError("Nessuna riga valida dopo i filtri (pezzi e colli devono essere ≥ 0).")

    return result


# ---------------------------------------------------------------------------
# Validazione / caricamento DataFrame
# ---------------------------------------------------------------------------

def valida_colonne(df: pd.DataFrame, required: set[str], nome: str) -> None:
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{nome}: colonne mancanti: {sorted(missing)}")


def prepara_cedi(df: pd.DataFrame) -> pd.DataFrame:
    """Valida e normalizza il DataFrame CEDI_SCADENZE.

    Richiede entrambe le colonne QTA_DISPONIBILE_COLLI e QTA_DISPONIBILE_PEZZI:
    - COLLI usata in modalità ceduto
    - PEZZI usata in modalità venduto
    """
    valida_colonne(
        df,
        {"LOTTO", "COD_ARTICOLO", "DESCRIZIONE_ARTICOLO",
         "QTA_DISPONIBILE_COLLI", "QTA_DISPONIBILE_PEZZI", "DATA_SCADENZA"},
        "CEDI_SCADENZE",
    )
    df = df.copy()
    df["LOTTO"] = df["LOTTO"].astype(str)
    df["COD_ARTICOLO"] = df["COD_ARTICOLO"].astype(str)
    df["DESCRIZIONE_ARTICOLO"] = df["DESCRIZIONE_ARTICOLO"].astype(str)
    df["DATA_SCADENZA"] = pd.to_datetime(df["DATA_SCADENZA"])
    df["QTA_DISPONIBILE_COLLI"] = pd.to_numeric(df["QTA_DISPONIBILE_COLLI"], errors="raise").fillna(0)
    df["QTA_DISPONIBILE_PEZZI"] = pd.to_numeric(df["QTA_DISPONIBILE_PEZZI"], errors="raise").fillna(0)
    return df


def prepara_ceduto_7gg(df: pd.DataFrame) -> pd.DataFrame:
    """Valida e normalizza il file ceduto CEDI — finestra 7 giorni."""
    valida_colonne(
        df,
        {"COD_PDV", "NOME_PDV", "COD_ARTICOLO", "QTA_CEDUTA_7GG_COLLI", "QTA_CEDUTA_7GG_PEZZI"},
        "CEDUTO_7GG",
    )
    df = df.copy()
    df["COD_PDV"] = df["COD_PDV"].astype(str)
    df["NOME_PDV"] = df["NOME_PDV"].astype(str)
    df["COD_ARTICOLO"] = df["COD_ARTICOLO"].astype(str)
    df["QTA_CEDUTA_7GG_COLLI"] = pd.to_numeric(df["QTA_CEDUTA_7GG_COLLI"], errors="raise").fillna(0)
    df["QTA_CEDUTA_7GG_PEZZI"] = pd.to_numeric(df["QTA_CEDUTA_7GG_PEZZI"], errors="raise").fillna(0)
    return df[["COD_PDV", "NOME_PDV", "COD_ARTICOLO", "QTA_CEDUTA_7GG_COLLI", "QTA_CEDUTA_7GG_PEZZI"]]


def prepara_ceduto_14gg(df: pd.DataFrame) -> pd.DataFrame:
    """Valida e normalizza il file ceduto CEDI — finestra 14 giorni."""
    valida_colonne(
        df,
        {"COD_PDV", "NOME_PDV", "COD_ARTICOLO", "QTA_CEDUTA_14GG_COLLI", "QTA_CEDUTA_14GG_PEZZI"},
        "CEDUTO_14GG",
    )
    df = df.copy()
    df["COD_PDV"] = df["COD_PDV"].astype(str)
    df["NOME_PDV"] = df["NOME_PDV"].astype(str)
    df["COD_ARTICOLO"] = df["COD_ARTICOLO"].astype(str)
    df["QTA_CEDUTA_14GG_COLLI"] = pd.to_numeric(df["QTA_CEDUTA_14GG_COLLI"], errors="raise").fillna(0)
    df["QTA_CEDUTA_14GG_PEZZI"] = pd.to_numeric(df["QTA_CEDUTA_14GG_PEZZI"], errors="raise").fillna(0)
    return df[["COD_PDV", "NOME_PDV", "COD_ARTICOLO", "QTA_CEDUTA_14GG_COLLI", "QTA_CEDUTA_14GG_PEZZI"]]


def prepara_ceduto_30gg(df: pd.DataFrame) -> pd.DataFrame:
    """Valida e normalizza il file ceduto CEDI — finestra 30 giorni."""
    valida_colonne(
        df,
        {"COD_PDV", "NOME_PDV", "COD_ARTICOLO", "QTA_CEDUTA_30GG_COLLI", "QTA_CEDUTA_30GG_PEZZI"},
        "CEDUTO_30GG",
    )
    df = df.copy()
    df["COD_PDV"] = df["COD_PDV"].astype(str)
    df["NOME_PDV"] = df["NOME_PDV"].astype(str)
    df["COD_ARTICOLO"] = df["COD_ARTICOLO"].astype(str)
    df["QTA_CEDUTA_30GG_COLLI"] = pd.to_numeric(df["QTA_CEDUTA_30GG_COLLI"], errors="raise").fillna(0)
    df["QTA_CEDUTA_30GG_PEZZI"] = pd.to_numeric(df["QTA_CEDUTA_30GG_PEZZI"], errors="raise").fillna(0)
    return df[["COD_PDV", "NOME_PDV", "COD_ARTICOLO", "QTA_CEDUTA_30GG_COLLI", "QTA_CEDUTA_30GG_PEZZI"]]


def prepara_ceduto_60gg(df: pd.DataFrame) -> pd.DataFrame:
    """Valida e normalizza il file ceduto CEDI — finestra 60 giorni (opzionale)."""
    valida_colonne(
        df,
        {"COD_PDV", "NOME_PDV", "COD_ARTICOLO", "QTA_CEDUTA_60GG_COLLI", "QTA_CEDUTA_60GG_PEZZI"},
        "CEDUTO_60GG",
    )
    df = df.copy()
    df["COD_PDV"] = df["COD_PDV"].astype(str)
    df["NOME_PDV"] = df["NOME_PDV"].astype(str)
    df["COD_ARTICOLO"] = df["COD_ARTICOLO"].astype(str)
    df["QTA_CEDUTA_60GG_COLLI"] = pd.to_numeric(df["QTA_CEDUTA_60GG_COLLI"], errors="raise").fillna(0)
    df["QTA_CEDUTA_60GG_PEZZI"] = pd.to_numeric(df["QTA_CEDUTA_60GG_PEZZI"], errors="raise").fillna(0)
    return df[["COD_PDV", "NOME_PDV", "COD_ARTICOLO", "QTA_CEDUTA_60GG_COLLI", "QTA_CEDUTA_60GG_PEZZI"]]


def unisci_ceduto(
    df_7: pd.DataFrame,
    df_14: pd.DataFrame | None,
    df_30: pd.DataFrame | None,
    df_60: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Fonde i DataFrame ceduto in un unico DataFrame con entrambe le varianti (COLLI/PEZZI).

    - df_7  è obbligatorio
    - df_14, df_30, df_60 sono opzionali; se assenti le rispettive QTA valgono 0

    In elabora_riallocazione() le colonne _COLLI o _PEZZI vengono selezionate
    in base alla modalità prima di calcolare l'indice di rotazione.
    """
    _CHIAVI = ["COD_PDV", "NOME_PDV", "COD_ARTICOLO"]
    df = df_7.copy()

    for n, df_n in [("14", df_14), ("30", df_30), ("60", df_60)]:
        colli_col = f"QTA_CEDUTA_{n}GG_COLLI"
        pezzi_col = f"QTA_CEDUTA_{n}GG_PEZZI"
        if df_n is not None and not df_n.empty:
            df = df.merge(df_n[_CHIAVI + [colli_col, pezzi_col]], on=_CHIAVI, how="left")
        else:
            df[colli_col] = 0.0
            df[pezzi_col] = 0.0

    # Colma i NaN prodotti dal left-join con 0
    qta_cols = [c for c in df.columns if c.startswith("QTA_CEDUTA_")]
    df[qta_cols] = df[qta_cols].fillna(0)
    return df


def prepara_vendite_pdv(df: pd.DataFrame) -> pd.DataFrame:
    """Valida e normalizza il DataFrame VENDITE_PDV.

    Richiede entrambe le colonne QTA_VENDUTA_MESE_COLLI e QTA_VENDUTA_MESE_PEZZI.
    In modalità venduto viene usata la colonna PEZZI.
    """
    valida_colonne(
        df,
        {"COD_PDV", "NOME_PDV", "COD_ARTICOLO", "QTA_VENDUTA_MESE_COLLI", "QTA_VENDUTA_MESE_PEZZI"},
        "VENDITE_PDV",
    )
    df = df.copy()
    df["COD_PDV"] = df["COD_PDV"].astype(str)
    df["NOME_PDV"] = df["NOME_PDV"].astype(str)
    df["COD_ARTICOLO"] = df["COD_ARTICOLO"].astype(str)
    df["QTA_VENDUTA_MESE_COLLI"] = pd.to_numeric(df["QTA_VENDUTA_MESE_COLLI"], errors="raise").fillna(0)
    df["QTA_VENDUTA_MESE_PEZZI"] = pd.to_numeric(df["QTA_VENDUTA_MESE_PEZZI"], errors="raise").fillna(0)
    return df


def prepara_anagrafica(df: pd.DataFrame) -> pd.DataFrame:
    """Valida e normalizza il DataFrame ANAGRAFICA_PDV."""
    valida_colonne(
        df,
        {"COD_PDV", "ATTIVO"},
        "ANAGRAFICA_PDV",
    )
    df = df.copy()
    df["COD_PDV"] = df["COD_PDV"].astype(str)
    # Normalizza ATTIVO a bool (accetta True/False, 1/0, "si"/"no", "true"/"false")
    _truthy = {"true", "1", "si", "yes", "s", "y"}
    df["ATTIVO"] = df["ATTIVO"].astype(str).str.strip().str.lower().isin(_truthy)
    return df


# ---------------------------------------------------------------------------
# Calcolo indice di rotazione
# ---------------------------------------------------------------------------

def calcola_indice_ceduto(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcola INDICE_ROT dal DataFrame ceduto già normalizzato (colonne generiche).

    Se QTA_CEDUTA_60GG è disponibile (> 0 su almeno una riga):
        INDICE_ROT = (Q7/7)×0.40 + (Q14/14)×0.25 + (Q30/30)×0.20 + (Q60/60)×0.15

    Altrimenti formula a 3 finestre (retrocompatibile):
        INDICE_ROT = (Q7/7)×0.50 + (Q14/14)×0.30 + (Q30/30)×0.20
    """
    df = df.copy()
    has_60 = "QTA_CEDUTA_60GG" in df.columns and (df["QTA_CEDUTA_60GG"] > 0).any()
    if has_60:
        df["INDICE_ROT"] = (
            (df["QTA_CEDUTA_7GG"]  / 7)  * 0.40
            + (df["QTA_CEDUTA_14GG"] / 14) * 0.25
            + (df["QTA_CEDUTA_30GG"] / 30) * 0.20
            + (df["QTA_CEDUTA_60GG"] / 60) * 0.15
        )
    else:
        df["INDICE_ROT"] = (
            (df["QTA_CEDUTA_7GG"]  / 7)  * 0.50
            + (df["QTA_CEDUTA_14GG"] / 14) * 0.30
            + (df["QTA_CEDUTA_30GG"] / 30) * 0.20
        )
    return df


def calcola_indice_venduto(df: pd.DataFrame) -> pd.DataFrame:
    """
    INDICE_ROT = QTA_VENDUTA_MESE / 30
    Il df deve avere la colonna QTA_VENDUTA_MESE (già normalizzata in elabora_riallocazione).
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
      - con INDICE_ROT < SOGLIA_INDICE_MIN
      - non attivi (se anagrafica disponibile)
    """
    df = pdv_df.copy()

    if anagrafica_df is not None and not anagrafica_df.empty:
        attivi = anagrafica_df.loc[anagrafica_df["ATTIVO"], "COD_PDV"]
        df = df[df["COD_PDV"].isin(attivi)]

    df = df[df["INDICE_ROT"] >= SOGLIA_INDICE_MIN]
    return df


# ---------------------------------------------------------------------------
# Priorità, motivo e sconto
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


def proponi_sconto(
    qta_non_allocata: float,
    qta_disponibile: float,
    giorni_residui: int,
) -> float | None:
    """
    Propone uno sconto percentuale (es. 0.25 = 25%) quando una quota significativa
    dello stock non riesce a essere allocata ai PDV entro la scadenza.

    Logica (soglie in ordine decrescente di urgenza):
      - giorni ≤ 2                              → 40%
      - giorni ≤ 5                              → 25%
      - giorni ≤ 10 e non-allocato > 40% stock  → 20%
      - giorni ≤ 15 e non-allocato > 25% stock  → 15%
      - giorni ≤ 20 e non-allocato > 15% stock  → 10%
      - altrimenti                              → None
    """
    if qta_non_allocata <= 0:
        return None
    frac = qta_non_allocata / qta_disponibile if qta_disponibile > 0 else 0.0
    if giorni_residui <= 2:
        return 0.40
    if giorni_residui <= 5:
        return 0.25
    if giorni_residui <= 10 and frac > 0.40:
        return 0.20
    if giorni_residui <= 15 and frac > 0.25:
        return 0.15
    if giorni_residui <= 20 and frac > 0.15:
        return 0.10
    return None


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
    """
    max_pdv = MAX_PDV_CRITICO if giorni_residui <= GIORNI_CRITICI else MAX_PDV_NORMALE

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

    Normalizzazione unità di misura:
      - modalita "ceduto" → usa colonne _COLLI e QTA_DISPONIBILE_COLLI
      - modalita "venduto" → usa colonne _PEZZI e QTA_DISPONIBILE_PEZZI

    Fallback per referenze senza storico:
      - se nessun PDV ha dati per quell'articolo, viene usata la media
        INDICE_ROT per PDV calcolata su tutti gli articoli disponibili.

    Returns:
        {"allocazioni": pd.DataFrame, "summary": dict, "avvisi": list[str]}
    """
    if data_riferimento is None:
        data_riferimento = date.today()

    # ── Normalizza colonne QTA in base alla modalità ──────────────────────
    cedi_df = cedi_df.copy()
    rotazione_df = rotazione_df.copy()

    if modalita == MODALITA_CEDUTO:
        um = "colli"
        cedi_df["QTA_DISPONIBILE"] = cedi_df["QTA_DISPONIBILE_COLLI"]
        rotazione_df = rotazione_df.rename(columns={
            "QTA_CEDUTA_7GG_COLLI":  "QTA_CEDUTA_7GG",
            "QTA_CEDUTA_14GG_COLLI": "QTA_CEDUTA_14GG",
            "QTA_CEDUTA_30GG_COLLI": "QTA_CEDUTA_30GG",
            "QTA_CEDUTA_60GG_COLLI": "QTA_CEDUTA_60GG",
        })
        rotazione_df = calcola_indice_ceduto(rotazione_df)
        coeff = COEFF_CEDUTO
    else:
        um = "pezzi"
        cedi_df["QTA_DISPONIBILE"] = cedi_df["QTA_DISPONIBILE_PEZZI"]
        rotazione_df = rotazione_df.rename(columns={
            "QTA_VENDUTA_MESE_PEZZI": "QTA_VENDUTA_MESE",
        })
        rotazione_df = calcola_indice_venduto(rotazione_df)
        coeff = COEFF_VENDUTO

    # ── Ordina lotti per urgenza (scadenza più vicina prima) ──────────────────
    cedi_df = cedi_df.sort_values("DATA_SCADENZA", ascending=True).reset_index(drop=True)

    # ── Pre-calcola la media INDICE_ROT per PDV (fallback referenze senza storico) ──
    media_per_pdv = (
        rotazione_df.groupby(["COD_PDV", "NOME_PDV"])["INDICE_ROT"]
        .mean()
        .reset_index()
    )

    righe_output: list[dict] = []
    avvisi: list[str] = []

    # Traccia la capacità già usata per ogni (articolo, PDV) — evita over-assignment
    # su più lotti dello stesso articolo verso lo stesso PDV
    pdv_capacita_usata: dict[str, dict[str, float]] = defaultdict(dict)

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

        usa_fallback = False
        if pdv_articolo.empty:
            # Fallback: usa la media INDICE_ROT per PDV su tutti gli articoli
            if media_per_pdv.empty:
                avvisi.append(f"Lotto {lotto} ({cod_articolo}): nessun dato di rotazione — saltato")
                continue
            pdv_articolo = media_per_pdv.copy()
            pdv_articolo["COD_ARTICOLO"] = cod_articolo
            usa_fallback = True
            avvisi.append(
                f"Lotto {lotto} ({cod_articolo}): nessun storico specifico — "
                "allocazione stimata su media PDV"
            )

        # Calcola capacità stimata
        pdv_articolo = calcola_capacita(pdv_articolo, giorni_residui, coeff)

        # Sottrai la capacità già usata da lotti precedenti dello stesso articolo
        gia_usata = pdv_capacita_usata[cod_articolo]
        if gia_usata:
            for idx in pdv_articolo.index:
                cod_pdv = str(pdv_articolo.at[idx, "COD_PDV"])
                used = gia_usata.get(cod_pdv, 0.0)
                pdv_articolo.at[idx, "CAPACITA_STIMATA"] = max(
                    0.0, pdv_articolo.at[idx, "CAPACITA_STIMATA"] - used
                )

        # Applica filtri PDV
        pdv_articolo = filtra_pdv(pdv_articolo, anagrafica_df)

        if pdv_articolo.empty:
            avvisi.append(f"Lotto {lotto} ({cod_articolo}): nessun PDV idoneo dopo i filtri")
            continue

        # Alloca la quantità disponibile
        allocazioni, qta_non_allocata = alloca_quantita(qta_disponibile, pdv_articolo, giorni_residui)

        # Aggiorna il tracking: registra quanto assegnato a ogni PDV per questo articolo
        for _, arow in allocazioni.iterrows():
            cod_pdv_str = str(arow["COD_PDV"])
            pdv_capacita_usata[cod_articolo][cod_pdv_str] = (
                pdv_capacita_usata[cod_articolo].get(cod_pdv_str, 0.0) + float(arow["QTA_PROPOSTA"])
            )

        if qta_non_allocata > 0:
            avvisi.append(
                f"Lotto {lotto} ({cod_articolo}): {qta_non_allocata:.0f} {um} non allocati"
            )

        priorita = assegna_priorita(giorni_residui)
        sconto = proponi_sconto(qta_non_allocata, qta_disponibile, giorni_residui)

        motivo_base = "(media PDV) " if usa_fallback else ""
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
                "UM": um,
                "PRIORITA": priorita,
                "MOTIVO": motivo_base + assegna_motivo(indice, capacita, giorni_residui),
                "MODALITA_CALCOLO": "Ceduto" if modalita == MODALITA_CEDUTO else "Venduto",
                "SCONTO_PROPOSTO": sconto,
            })

    if not righe_output:
        output_df = pd.DataFrame(columns=[
            "LOTTO", "COD_ARTICOLO", "DESCRIZIONE_ARTICOLO", "COD_PDV", "NOME_PDV",
            "GIORNI_RESIDUI", "INDICE_ROT", "CAPACITA_STIMATA", "QTA_PROPOSTA",
            "UM", "PRIORITA", "MOTIVO", "MODALITA_CALCOLO", "SCONTO_PROPOSTO",
        ])
    else:
        output_df = pd.DataFrame(righe_output)

        priorita_order = {"Alta": 0, "Media": 1, "Bassa": 2}
        output_df["_pord"] = output_df["PRIORITA"].map(priorita_order)
        output_df = (
            output_df.sort_values(["_pord", "CAPACITA_STIMATA"], ascending=[True, False])
            .drop(columns=["_pord"])
            .reset_index(drop=True)
        )

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
    """Calcola le statistiche di riepilogo per la Dashboard.

    Usa QTA_DISPONIBILE che è stata normalizzata (colli o pezzi) in elabora_riallocazione.
    """
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

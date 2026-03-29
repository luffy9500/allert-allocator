"""
Motore di calcolo per la riallocazione di prodotti in scadenza.
Da CEDI (Centro Distribuzione) verso PDV (Punti di Vendita).
"""

import pandas as pd
from datetime import date
import sys


def load_cedi_scadenze(path: str) -> pd.DataFrame:
    """Carica e valida il file CEDI_SCADENZE."""
    df = pd.read_excel(path)

    required = {"LOTTO", "COD_ARTICOLO", "DESCRIZIONE_ARTICOLO", "QTA_DISPONIBILE", "DATA_SCADENZA"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CEDI_SCADENZE: colonne mancanti: {missing}")

    df["DATA_SCADENZA"] = pd.to_datetime(df["DATA_SCADENZA"])
    df["QTA_DISPONIBILE"] = pd.to_numeric(df["QTA_DISPONIBILE"], errors="raise")
    return df


def load_vendite_pdv(path: str) -> pd.DataFrame:
    """Carica e valida il file VENDITE_PDV_STORICO."""
    df = pd.read_excel(path)

    required = {"COD_PDV", "NOME_PDV", "COD_ARTICOLO", "QTA_VENDUTA_30GG", "QTA_VENDUTA_15GG", "QTA_VENDUTA_7GG"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"VENDITE_PDV_STORICO: colonne mancanti: {missing}")

    for col in ("QTA_VENDUTA_30GG", "QTA_VENDUTA_15GG", "QTA_VENDUTA_7GG"):
        df[col] = pd.to_numeric(df[col], errors="raise")
    return df


def calcola_indice_rotazione(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcola l'indice di rotazione per ogni riga del dataframe vendite.

    Formula:
        INDICE_ROTAZIONE = (QTA_VENDUTA_7GG/7 * 0.5)
                         + (QTA_VENDUTA_15GG/15 * 0.3)
                         + (QTA_VENDUTA_30GG/30 * 0.2)
    """
    df = df.copy()
    df["INDICE_ROTAZIONE"] = (
        (df["QTA_VENDUTA_7GG"] / 7) * 0.5
        + (df["QTA_VENDUTA_15GG"] / 15) * 0.3
        + (df["QTA_VENDUTA_30GG"] / 30) * 0.2
    )
    return df


def calcola_capacita_stimata(df: pd.DataFrame, giorni_residui: int) -> pd.DataFrame:
    """
    Calcola la capacità stimata di assorbimento di un PDV in base ai giorni residui.

    Formula:
        CAPACITA_STIMATA = INDICE_ROTAZIONE × GIORNI_RESIDUI × 0.8
    """
    df = df.copy()
    df["GIORNI_RESIDUI"] = giorni_residui
    df["CAPACITA_STIMATA"] = df["INDICE_ROTAZIONE"] * giorni_residui * 0.8
    return df


def alloca_quantita(qta_disponibile: float, pdv_df: pd.DataFrame) -> pd.DataFrame:
    """
    Alloca la quantità disponibile ai PDV in ordine di CAPACITA_STIMATA decrescente.
    Ogni PDV riceve al massimo la propria CAPACITA_STIMATA.
    La distribuzione si interrompe quando la quantità è esaurita.
    """
    # Ordina dal PDV con maggiore capacità al minore
    pdv_ordinati = pdv_df.sort_values("CAPACITA_STIMATA", ascending=False).copy()
    pdv_ordinati["QTA_PROPOSTA"] = 0.0

    rimanente = qta_disponibile

    for idx in pdv_ordinati.index:
        if rimanente <= 0:
            break
        capacita = pdv_ordinati.at[idx, "CAPACITA_STIMATA"]
        assegnato = min(capacita, rimanente)
        pdv_ordinati.at[idx, "QTA_PROPOSTA"] = assegnato
        rimanente -= assegnato

    # Restituisce solo i PDV a cui è stata assegnata almeno una unità
    return pdv_ordinati[pdv_ordinati["QTA_PROPOSTA"] > 0]


def elabora_riallocazione(
    path_cedi: str,
    path_vendite: str,
    path_output: str,
    data_riferimento: date | None = None,
) -> pd.DataFrame:
    """
    Funzione principale: carica i dati, calcola le allocazioni e salva l'output.

    Args:
        path_cedi:        percorso file Excel CEDI_SCADENZE
        path_vendite:     percorso file Excel VENDITE_PDV_STORICO
        path_output:      percorso file Excel di output
        data_riferimento: data da usare come "oggi" (default: date.today())

    Returns:
        DataFrame con le riallocazioni proposte.
    """
    if data_riferimento is None:
        data_riferimento = date.today()

    # --- Caricamento ---
    cedi = load_cedi_scadenze(path_cedi)
    vendite = load_vendite_pdv(path_vendite)

    # --- Calcolo indice di rotazione (a livello PDV/articolo) ---
    vendite = calcola_indice_rotazione(vendite)

    righe_output = []

    for _, lotto_row in cedi.iterrows():
        lotto = lotto_row["LOTTO"]
        cod_articolo = lotto_row["COD_ARTICOLO"]
        descrizione = lotto_row["DESCRIZIONE_ARTICOLO"]
        qta_disponibile = lotto_row["QTA_DISPONIBILE"]
        data_scadenza = lotto_row["DATA_SCADENZA"].date()

        # Calcola i giorni residui alla scadenza
        giorni_residui = (data_scadenza - data_riferimento).days

        if giorni_residui <= 0:
            # Prodotto già scaduto: salta
            print(f"[SKIP] Lotto {lotto} ({cod_articolo}) già scaduto ({data_scadenza})")
            continue

        # Filtra i PDV che vendono questo articolo
        pdv_articolo = vendite[vendite["COD_ARTICOLO"] == cod_articolo].copy()

        if pdv_articolo.empty:
            print(f"[WARN] Nessun PDV trovato per l'articolo {cod_articolo} (lotto {lotto})")
            continue

        # Calcola la capacità stimata per ciascun PDV
        pdv_articolo = calcola_capacita_stimata(pdv_articolo, giorni_residui)

        # Alloca le quantità
        allocazioni = alloca_quantita(qta_disponibile, pdv_articolo)

        for _, pdv_row in allocazioni.iterrows():
            righe_output.append({
                "LOTTO": lotto,
                "COD_ARTICOLO": cod_articolo,
                "DESCRIZIONE_ARTICOLO": descrizione,
                "COD_PDV": pdv_row["COD_PDV"],
                "NOME_PDV": pdv_row["NOME_PDV"],
                "GIORNI_RESIDUI": giorni_residui,
                "INDICE_ROTAZIONE": round(pdv_row["INDICE_ROTAZIONE"], 4),
                "CAPACITA_STIMATA": round(pdv_row["CAPACITA_STIMATA"], 2),
                "QTA_PROPOSTA": round(pdv_row["QTA_PROPOSTA"], 2),
            })

    if not righe_output:
        print("[INFO] Nessuna riallocazione da produrre.")
        return pd.DataFrame()

    output_df = pd.DataFrame(righe_output)

    # Ordinamento finale: articolo, giorni residui crescente, capacità decrescente
    output_df = output_df.sort_values(
        ["COD_ARTICOLO", "GIORNI_RESIDUI", "CAPACITA_STIMATA"],
        ascending=[True, True, False],
    ).reset_index(drop=True)

    # --- Salvataggio ---
    output_df.to_excel(path_output, index=False)
    print(f"[OK] Output salvato in: {path_output} ({len(output_df)} righe)")

    return output_df


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python allert_allocator.py <CEDI_SCADENZE.xlsx> <VENDITE_PDV_STORICO.xlsx> <OUTPUT.xlsx>")
        sys.exit(1)

    elabora_riallocazione(
        path_cedi=sys.argv[1],
        path_vendite=sys.argv[2],
        path_output=sys.argv[3],
    )

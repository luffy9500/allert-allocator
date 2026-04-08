"""
Test per backend/engine.py.
Copre entrambe le modalità (ceduto / venduto), filtri PDV, casi critici e summary.
"""

import io

import pytest
import pandas as pd
from datetime import date, timedelta

from backend.engine import (
    prepara_cedi,
    prepara_ceduto_7gg,
    prepara_ceduto_14gg,
    prepara_ceduto_30gg,
    prepara_ceduto_60gg,
    prepara_vendite_pdv,
    prepara_anagrafica,
    calcola_indice_ceduto,
    calcola_indice_venduto,
    calcola_capacita,
    filtra_pdv,
    assegna_priorita,
    assegna_motivo,
    proponi_sconto,
    alloca_quantita,
    unisci_ceduto,
    elabora_riallocazione,
    trasforma_ceduto_raw,
    rileva_periodo_ceduto,
    COEFF_CEDUTO,
    COEFF_VENDUTO,
    SOGLIA_INDICE_MIN,
    GIORNI_CRITICI,
    MAX_PDV_CRITICO,
    MAX_PDV_NORMALE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cedi(giorni=10, qta_colli=100.0, qta_pezzi=600.0, cod="ART001"):
    return pd.DataFrame([{
        "LOTTO": "L001",
        "COD_ARTICOLO": cod,
        "DESCRIZIONE_ARTICOLO": "Yogurt Bianco",
        "QTA_DISPONIBILE_COLLI": qta_colli,
        "QTA_DISPONIBILE_PEZZI": qta_pezzi,
        "DATA_SCADENZA": pd.Timestamp(date.today() + timedelta(days=giorni)),
    }])


def _ceduto_7(cod="ART001", q7c=14, q7p=84, cod_pdv="PDV01", nome="Super A"):
    return pd.DataFrame([{
        "COD_PDV": cod_pdv, "NOME_PDV": nome, "COD_ARTICOLO": cod,
        "QTA_CEDUTA_7GG_COLLI": q7c, "QTA_CEDUTA_7GG_PEZZI": q7p,
    }])


def _ceduto_14(cod="ART001", q14c=28, q14p=168, cod_pdv="PDV01", nome="Super A"):
    return pd.DataFrame([{
        "COD_PDV": cod_pdv, "NOME_PDV": nome, "COD_ARTICOLO": cod,
        "QTA_CEDUTA_14GG_COLLI": q14c, "QTA_CEDUTA_14GG_PEZZI": q14p,
    }])


def _ceduto_30(cod="ART001", q30c=60, q30p=360, cod_pdv="PDV01", nome="Super A"):
    return pd.DataFrame([{
        "COD_PDV": cod_pdv, "NOME_PDV": nome, "COD_ARTICOLO": cod,
        "QTA_CEDUTA_30GG_COLLI": q30c, "QTA_CEDUTA_30GG_PEZZI": q30p,
    }])


def _ceduto_60(cod="ART001", q60c=120, q60p=720, cod_pdv="PDV01", nome="Super A"):
    return pd.DataFrame([{
        "COD_PDV": cod_pdv, "NOME_PDV": nome, "COD_ARTICOLO": cod,
        "QTA_CEDUTA_60GG_COLLI": q60c, "QTA_CEDUTA_60GG_PEZZI": q60p,
    }])


def _ceduto(cod="ART001", q7c=14, q14c=28, q30c=60, q7p=84, q14p=168, q30p=360,
            cod_pdv="PDV01", nome="Super A"):
    """Helper che costruisce il DataFrame ceduto unificato (già mergiato)."""
    df7  = prepara_ceduto_7gg(_ceduto_7(cod=cod, q7c=q7c, q7p=q7p, cod_pdv=cod_pdv, nome=nome))
    df14 = prepara_ceduto_14gg(_ceduto_14(cod=cod, q14c=q14c, q14p=q14p, cod_pdv=cod_pdv, nome=nome))
    df30 = prepara_ceduto_30gg(_ceduto_30(cod=cod, q30c=q30c, q30p=q30p, cod_pdv=cod_pdv, nome=nome))
    return unisci_ceduto(df7, df14, df30)


def _vendite(cod="ART001", mese_colli=15, mese_pezzi=90, cod_pdv="PDV01", nome="Super A"):
    return pd.DataFrame([{
        "COD_PDV": cod_pdv, "NOME_PDV": nome,
        "COD_ARTICOLO": cod,
        "QTA_VENDUTA_MESE_COLLI": mese_colli,
        "QTA_VENDUTA_MESE_PEZZI": mese_pezzi,
    }])


def _anagrafica(cod_pdv="PDV01", attivo=True):
    return pd.DataFrame([{
        "COD_PDV": cod_pdv, "NOME_PDV": "Super A",
        "CLUSTER_PDV": "A", "FORMATO_PDV": "Super",
        "AREA_GEOGRAFICA": "Nord", "ATTIVO": attivo,
    }])


# ---------------------------------------------------------------------------
# Validazione colonne
# ---------------------------------------------------------------------------

class TestValidazione:

    def test_cedi_colonne_mancanti(self):
        df = pd.DataFrame([{"LOTTO": "L1"}])
        with pytest.raises(ValueError, match="CEDI_SCADENZE"):
            prepara_cedi(df)

    def test_ceduto_7gg_colonne_mancanti(self):
        df = pd.DataFrame([{"COD_PDV": "P1"}])
        with pytest.raises(ValueError, match="CEDUTO_7GG"):
            prepara_ceduto_7gg(df)

    def test_ceduto_14gg_colonne_mancanti(self):
        df = pd.DataFrame([{"COD_PDV": "P1"}])
        with pytest.raises(ValueError, match="CEDUTO_14GG"):
            prepara_ceduto_14gg(df)

    def test_ceduto_30gg_colonne_mancanti(self):
        df = pd.DataFrame([{"COD_PDV": "P1"}])
        with pytest.raises(ValueError, match="CEDUTO_30GG"):
            prepara_ceduto_30gg(df)

    def test_ceduto_60gg_colonne_mancanti(self):
        df = pd.DataFrame([{"COD_PDV": "P1"}])
        with pytest.raises(ValueError, match="CEDUTO_60GG"):
            prepara_ceduto_60gg(df)

    def test_vendite_colonne_mancanti(self):
        df = pd.DataFrame([{"COD_PDV": "P1"}])
        with pytest.raises(ValueError, match="VENDITE_PDV"):
            prepara_vendite_pdv(df)

    def test_anagrafica_attivo_stringa(self):
        df = pd.DataFrame([{"COD_PDV": "P1", "ATTIVO": "si"}])
        result = prepara_anagrafica(df)
        assert result["ATTIVO"].iloc[0] == True

    def test_anagrafica_attivo_no(self):
        df = pd.DataFrame([{"COD_PDV": "P1", "ATTIVO": "no"}])
        result = prepara_anagrafica(df)
        assert result["ATTIVO"].iloc[0] == False


# ---------------------------------------------------------------------------
# Trasformazione file ceduto raw
# ---------------------------------------------------------------------------

def _make_raw_ceduto_bytes(data_rows: list[list], n_cols: int = 20) -> bytes:
    """Crea bytes Excel con 1 riga header + data_rows nel formato grezzo."""
    header = [f"H{i}" for i in range(n_cols)]
    all_rows = [header] + data_rows
    df = pd.DataFrame(all_rows)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, header=False)
    return buf.getvalue()


def _raw_row(radice=30264, variante=1, tipo="L", pezzi=70, imballo=7, cod_pdv=20873, nome="SUPER MKT"):
    """Crea una riga raw con i valori nelle colonne corrette."""
    row = [""] * 20
    row[9]  = radice
    row[10] = variante
    row[12] = tipo
    row[14] = pezzi
    row[15] = imballo
    row[17] = cod_pdv
    row[18] = nome
    return row


class TestTrasformaCedutoRaw:

    def test_trasformazione_base(self):
        content = _make_raw_ceduto_bytes([_raw_row()])
        df = trasforma_ceduto_raw(content, "7GG")
        assert "COD_ARTICOLO" in df.columns
        assert "QTA_CEDUTA_7GG_COLLI" in df.columns
        assert "QTA_CEDUTA_7GG_PEZZI" in df.columns
        assert df.iloc[0]["COD_ARTICOLO"] == "3026401"   # 30264 + "01"
        assert df.iloc[0]["QTA_CEDUTA_7GG_COLLI"] == 10  # round(70/7)
        assert df.iloc[0]["QTA_CEDUTA_7GG_PEZZI"] == 70

    def test_periodo_nei_nomi_colonne(self):
        content = _make_raw_ceduto_bytes([_raw_row()])
        df14 = trasforma_ceduto_raw(content, "14GG")
        assert "QTA_CEDUTA_14GG_COLLI" in df14.columns

    def test_filtra_tipo_movimento_non_L(self):
        rows = [_raw_row(tipo="L"), _raw_row(tipo="O"), _raw_row(tipo="X")]
        content = _make_raw_ceduto_bytes(rows)
        df = trasforma_ceduto_raw(content, "7GG")
        assert len(df) == 1  # solo la riga L

    def test_filtra_header_ripetuto_col9_non_numerico(self):
        rows = [
            _raw_row(radice=30264),
            _raw_row(radice="Radice"),   # header ripetuto → da scartare
        ]
        content = _make_raw_ceduto_bytes(rows)
        df = trasforma_ceduto_raw(content, "7GG")
        assert len(df) == 1

    def test_normalizza_pdv_6_cifre_con_zero(self):
        row = _raw_row(cod_pdv=208750)   # 6 cifre, finisce con 0 → 20875
        content = _make_raw_ceduto_bytes([row])
        df = trasforma_ceduto_raw(content, "7GG")
        assert df.iloc[0]["COD_PDV"] == "20875"

    def test_pdv_5_cifre_invariato(self):
        row = _raw_row(cod_pdv=20873)
        content = _make_raw_ceduto_bytes([row])
        df = trasforma_ceduto_raw(content, "7GG")
        assert df.iloc[0]["COD_PDV"] == "20873"

    def test_imballo_zero_usa_uno(self):
        row = _raw_row(pezzi=50, imballo=0)   # imballo=0 → usa 1 → colli=50
        content = _make_raw_ceduto_bytes([row])
        df = trasforma_ceduto_raw(content, "7GG")
        assert df.iloc[0]["QTA_CEDUTA_7GG_COLLI"] == 50

    def test_filtra_pezzi_negativi(self):
        rows = [_raw_row(pezzi=70), _raw_row(pezzi=-10)]
        content = _make_raw_ceduto_bytes(rows)
        df = trasforma_ceduto_raw(content, "7GG")
        assert len(df) == 1

    def test_variante_zero_pad(self):
        row = _raw_row(radice=30264, variante=5)  # variante "5" → "05"
        content = _make_raw_ceduto_bytes([row])
        df = trasforma_ceduto_raw(content, "7GG")
        assert df.iloc[0]["COD_ARTICOLO"] == "3026405"

    def test_multifoglio(self):
        row1 = _raw_row(radice=11111, variante=1)
        row2 = _raw_row(radice=22222, variante=2)
        # Crea Excel con 2 fogli
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            pd.DataFrame([["H"] * 20, row1]).to_excel(writer, sheet_name="Fog1", index=False, header=False)
            pd.DataFrame([["H"] * 20, row2]).to_excel(writer, sheet_name="Fog2", index=False, header=False)
        content = buf.getvalue()
        df = trasforma_ceduto_raw(content, "7GG")
        articoli = set(df["COD_ARTICOLO"])
        assert "1111101" in articoli
        assert "2222202" in articoli

    def test_compatibile_con_prepara_ceduto_7gg(self):
        """Il DataFrame prodotto deve superare prepara_ceduto_7gg."""
        content = _make_raw_ceduto_bytes([_raw_row()])
        df_raw = trasforma_ceduto_raw(content, "7GG")
        df_ok = prepara_ceduto_7gg(df_raw)   # non deve sollevare ValueError
        assert len(df_ok) == 1


class TestRilevaPeriodoCeduto:

    def test_7gg_con_underscore(self):
        assert rileva_periodo_ceduto("CEDUTO_MAG_7_GG.XLS") == "7GG"

    def test_14gg_senza_separatore(self):
        assert rileva_periodo_ceduto("CEDUTO14GG.xlsx") == "14GG"

    def test_30gg_con_spazio(self):
        assert rileva_periodo_ceduto("ceduto 30 GG.xls") == "30GG"

    def test_60gg_case_insensitive(self):
        assert rileva_periodo_ceduto("file_60gg_export.xlsx") == "60GG"

    def test_default_senza_periodo(self):
        assert rileva_periodo_ceduto("file_senza_periodo.xls") == "7GG"

    def test_ignora_numeri_non_validi(self):
        assert rileva_periodo_ceduto("CEDUTO_45GG.xlsx") == "7GG"  # 45 non è valido


# ---------------------------------------------------------------------------
# Calcolo indice rotazione
# ---------------------------------------------------------------------------

class TestIndiceRotazione:

    def test_ceduto_formula_3_finestre(self):
        # Senza 60gg: (14/7)*0.5 + (28/14)*0.3 + (60/30)*0.2 = 1.0+0.6+0.4 = 2.0
        df = _ceduto(q7c=14, q14c=28, q30c=60)
        # Normalizza come fa elabora_riallocazione in modalità ceduto
        df2 = df.rename(columns={
            "QTA_CEDUTA_7GG_COLLI": "QTA_CEDUTA_7GG",
            "QTA_CEDUTA_14GG_COLLI": "QTA_CEDUTA_14GG",
            "QTA_CEDUTA_30GG_COLLI": "QTA_CEDUTA_30GG",
        })
        result = calcola_indice_ceduto(df2)
        assert result["INDICE_ROT"].iloc[0] == pytest.approx(2.0)

    def test_ceduto_unitario_3_finestre(self):
        # (7/7)*0.5 + (14/14)*0.3 + (30/30)*0.2 = 1.0
        df = _ceduto(q7c=7, q14c=14, q30c=30)
        df2 = df.rename(columns={
            "QTA_CEDUTA_7GG_COLLI": "QTA_CEDUTA_7GG",
            "QTA_CEDUTA_14GG_COLLI": "QTA_CEDUTA_14GG",
            "QTA_CEDUTA_30GG_COLLI": "QTA_CEDUTA_30GG",
        })
        result = calcola_indice_ceduto(df2)
        assert result["INDICE_ROT"].iloc[0] == pytest.approx(1.0)

    def test_ceduto_formula_4_finestre(self):
        # (7/7)*0.40 + (14/14)*0.25 + (30/30)*0.20 + (60/60)*0.15 = 1.0
        df = pd.DataFrame([{
            "QTA_CEDUTA_7GG": 7, "QTA_CEDUTA_14GG": 14,
            "QTA_CEDUTA_30GG": 30, "QTA_CEDUTA_60GG": 60,
        }])
        result = calcola_indice_ceduto(df)
        assert result["INDICE_ROT"].iloc[0] == pytest.approx(1.0)

    def test_venduto_formula(self):
        df = pd.DataFrame([{"COD_PDV": "P1", "NOME_PDV": "A",
                            "COD_ARTICOLO": "X", "QTA_VENDUTA_MESE": 90}])
        result = calcola_indice_venduto(df)
        assert result["INDICE_ROT"].iloc[0] == pytest.approx(3.0)

    def test_venduto_zero(self):
        df = pd.DataFrame([{"COD_PDV": "P1", "NOME_PDV": "A",
                            "COD_ARTICOLO": "X", "QTA_VENDUTA_MESE": 0}])
        result = calcola_indice_venduto(df)
        assert result["INDICE_ROT"].iloc[0] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Capacità stimata
# ---------------------------------------------------------------------------

class TestCapacita:

    def test_ceduto_coeff(self):
        df = pd.DataFrame([{"INDICE_ROT": 2.0}])
        result = calcola_capacita(df, giorni_residui=10, coeff=COEFF_CEDUTO)
        assert result["CAPACITA_STIMATA"].iloc[0] == pytest.approx(2.0 * 10 * 0.7)

    def test_venduto_coeff(self):
        df = pd.DataFrame([{"INDICE_ROT": 3.0}])
        result = calcola_capacita(df, giorni_residui=10, coeff=COEFF_VENDUTO)
        assert result["CAPACITA_STIMATA"].iloc[0] == pytest.approx(3.0 * 10 * 0.8)


# ---------------------------------------------------------------------------
# Filtro PDV
# ---------------------------------------------------------------------------

class TestFiltroPDV:

    def _pdv_df(self, indice):
        return pd.DataFrame([{"COD_PDV": "P1", "NOME_PDV": "A",
                               "INDICE_ROT": indice, "CAPACITA_STIMATA": 10}])

    def test_esclude_indice_sotto_soglia(self):
        df = self._pdv_df(SOGLIA_INDICE_MIN - 0.01)
        assert filtra_pdv(df, None).empty

    def test_include_indice_uguale_soglia(self):
        df = self._pdv_df(SOGLIA_INDICE_MIN)
        assert len(filtra_pdv(df, None)) == 1

    def test_esclude_pdv_non_attivo(self):
        pdv = self._pdv_df(1.0)
        anag = _anagrafica(cod_pdv="P1", attivo=False)
        assert filtra_pdv(pdv, prepara_anagrafica(anag)).empty

    def test_include_pdv_attivo(self):
        pdv = self._pdv_df(1.0)
        anag = _anagrafica(cod_pdv="P1", attivo=True)
        assert len(filtra_pdv(pdv, prepara_anagrafica(anag))) == 1

    def test_anagrafica_none_non_filtra_attivita(self):
        assert len(filtra_pdv(self._pdv_df(1.0), None)) == 1


# ---------------------------------------------------------------------------
# Priorità, motivo e sconto
# ---------------------------------------------------------------------------

class TestPrioritaMotivo:

    def test_priorita_alta(self):
        assert assegna_priorita(5) == "Alta"

    def test_priorita_media(self):
        assert assegna_priorita(10) == "Media"

    def test_priorita_bassa(self):
        assert assegna_priorita(20) == "Bassa"

    def test_motivo_critico(self):
        assert assegna_motivo(2.0, 10.0, GIORNI_CRITICI) == "Prodotto critico"

    def test_motivo_alta_rotazione(self):
        assert assegna_motivo(1.5, 20.0, 10) == "Alta rotazione"

    def test_motivo_bassa_capacita(self):
        assert assegna_motivo(0.3, 3.0, 10) == "Bassa capacità"

    def test_motivo_standard(self):
        assert assegna_motivo(1.0, 10.0, 10) == "Rotazione standard"


class TestProponiSconto:

    def test_nessuno_sconto_se_tutto_allocato(self):
        assert proponi_sconto(0.0, 100.0, 3) is None

    def test_sconto_40_giorni_critici(self):
        assert proponi_sconto(50.0, 100.0, 2) == pytest.approx(0.40)

    def test_sconto_25_giorni_5(self):
        assert proponi_sconto(10.0, 100.0, 5) == pytest.approx(0.25)

    def test_sconto_20_alta_frazione_giorni_10(self):
        # frac=0.50 > 0.40 → 20%
        assert proponi_sconto(50.0, 100.0, 10) == pytest.approx(0.20)

    def test_sconto_20_non_scatta_frac_bassa_giorni_10(self):
        # frac=0.30 ≤ 0.40 → nessun 20%; ma giorni=10 ≤ 15 e frac=0.30 > 0.25 → 15%
        assert proponi_sconto(30.0, 100.0, 10) == pytest.approx(0.15)

    def test_sconto_15_media_frazione_giorni_15(self):
        # giorni=15 ≤ 15 e frac=0.30 > 0.25 → 15%
        assert proponi_sconto(30.0, 100.0, 15) == pytest.approx(0.15)

    def test_sconto_10_bassa_frazione_giorni_20(self):
        # giorni=20 ≤ 20 e frac=0.20 > 0.15 → 10%
        assert proponi_sconto(20.0, 100.0, 20) == pytest.approx(0.10)

    def test_nessuno_sconto_bassa_urgenza(self):
        # giorni=21 > 20 → None
        assert proponi_sconto(20.0, 100.0, 21) is None

    def test_nessuno_sconto_frac_troppo_bassa(self):
        # giorni=20 ma frac=0.10 ≤ 0.15 → None
        assert proponi_sconto(10.0, 100.0, 20) is None


# ---------------------------------------------------------------------------
# Allocazione quantità
# ---------------------------------------------------------------------------

class TestAllocaQuantita:

    def _pdv(self, cap_list):
        return pd.DataFrame([
            {"COD_PDV": f"P{i}", "NOME_PDV": f"PDV {i}",
             "CAPACITA_STIMATA": c, "INDICE_ROT": c / 10}
            for i, c in enumerate(cap_list, 1)
        ])

    def test_allocazione_singolo_pdv(self):
        alloc, non_alloc = alloca_quantita(30.0, self._pdv([50.0]), giorni_residui=10)
        assert int(alloc["QTA_PROPOSTA"].sum()) == 30
        assert non_alloc == pytest.approx(0.0)

    def test_quantita_non_allocata(self):
        _, non_alloc = alloca_quantita(20.0, self._pdv([10.0]), giorni_residui=10)
        assert non_alloc > 0

    def test_max_pdv_normale(self):
        alloc, _ = alloca_quantita(200.0, self._pdv([10.0] * 15), giorni_residui=10)
        assert len(alloc) <= MAX_PDV_NORMALE

    def test_max_pdv_critico(self):
        alloc, _ = alloca_quantita(200.0, self._pdv([10.0] * 10), giorni_residui=GIORNI_CRITICI)
        assert len(alloc) <= MAX_PDV_CRITICO

    def test_non_assegna_meno_di_uno(self):
        alloc, _ = alloca_quantita(1.0, self._pdv([0.5]), giorni_residui=10)
        assert alloc.empty or (alloc["QTA_PROPOSTA"] >= 1).all()

    def test_ordine_decrescente_capacita(self):
        alloc, _ = alloca_quantita(20.0, self._pdv([5.0, 30.0, 15.0]), giorni_residui=10)
        assert alloc.iloc[0]["COD_PDV"] == "P2"


# ---------------------------------------------------------------------------
# Merge ceduto: unisci_ceduto()
# ---------------------------------------------------------------------------

class TestUnisciCeduto:

    def test_tutti_e_quattro_presenti(self):
        df7  = prepara_ceduto_7gg(_ceduto_7(q7c=7, q7p=42))
        df14 = prepara_ceduto_14gg(_ceduto_14(q14c=14, q14p=84))
        df30 = prepara_ceduto_30gg(_ceduto_30(q30c=30, q30p=180))
        df60 = prepara_ceduto_60gg(_ceduto_60(q60c=60, q60p=360))
        merged = unisci_ceduto(df7, df14, df30, df60)
        assert "QTA_CEDUTA_7GG_COLLI"  in merged.columns
        assert "QTA_CEDUTA_60GG_PEZZI" in merged.columns
        assert merged["QTA_CEDUTA_60GG_COLLI"].iloc[0] == 60

    def test_solo_7gg_obbligatorio(self):
        df7 = prepara_ceduto_7gg(_ceduto_7(q7c=21, q7p=126))
        merged = unisci_ceduto(df7, None, None)
        assert merged["QTA_CEDUTA_7GG_COLLI"].iloc[0] == 21
        assert merged["QTA_CEDUTA_14GG_COLLI"].iloc[0] == 0.0
        assert merged["QTA_CEDUTA_30GG_COLLI"].iloc[0] == 0.0
        assert merged["QTA_CEDUTA_60GG_COLLI"].iloc[0] == 0.0

    def test_senza_60gg(self):
        df7  = prepara_ceduto_7gg(_ceduto_7(q7c=7, q7p=42))
        df14 = prepara_ceduto_14gg(_ceduto_14(q14c=14, q14p=84))
        merged = unisci_ceduto(df7, df14, None)
        assert merged["QTA_CEDUTA_60GG_COLLI"].iloc[0] == 0.0

    def test_merge_preserva_tutti_i_pdv(self):
        df7 = prepara_ceduto_7gg(pd.DataFrame([
            {"COD_PDV": "P1", "NOME_PDV": "A", "COD_ARTICOLO": "ART1",
             "QTA_CEDUTA_7GG_COLLI": 7, "QTA_CEDUTA_7GG_PEZZI": 42},
            {"COD_PDV": "P2", "NOME_PDV": "B", "COD_ARTICOLO": "ART1",
             "QTA_CEDUTA_7GG_COLLI": 14, "QTA_CEDUTA_7GG_PEZZI": 84},
        ]))
        df14 = prepara_ceduto_14gg(pd.DataFrame([
            {"COD_PDV": "P1", "NOME_PDV": "A", "COD_ARTICOLO": "ART1",
             "QTA_CEDUTA_14GG_COLLI": 10, "QTA_CEDUTA_14GG_PEZZI": 60},
        ]))
        merged = unisci_ceduto(df7, df14, None)
        assert len(merged) == 2
        p2 = merged[merged["COD_PDV"] == "P2"]
        assert p2["QTA_CEDUTA_14GG_COLLI"].iloc[0] == 0.0  # left-join → 0


# ---------------------------------------------------------------------------
# Integrazione: elabora_riallocazione
# ---------------------------------------------------------------------------

class TestElaboraRiallocazione:

    def test_modalita_ceduto_colonne_output(self):
        cedi = prepara_cedi(_cedi(giorni=10, qta_colli=50))
        ceduto = _ceduto()
        result = elabora_riallocazione(cedi, ceduto, None, "ceduto")
        df = result["allocazioni"]
        expected = {
            "LOTTO", "COD_ARTICOLO", "DESCRIZIONE_ARTICOLO", "COD_PDV", "NOME_PDV",
            "GIORNI_RESIDUI", "INDICE_ROT", "CAPACITA_STIMATA", "QTA_PROPOSTA",
            "UM", "PRIORITA", "MOTIVO", "MODALITA_CALCOLO", "SCONTO_PROPOSTO",
        }
        assert expected == set(df.columns)

    def test_modalita_ceduto_um_colli(self):
        cedi = prepara_cedi(_cedi(giorni=10, qta_colli=50))
        result = elabora_riallocazione(cedi, _ceduto(), None, "ceduto")
        df = result["allocazioni"]
        if not df.empty:
            assert (df["UM"] == "colli").all()

    def test_modalita_venduto_um_pezzi(self):
        cedi = prepara_cedi(_cedi(giorni=10, qta_pezzi=300))
        vendite = prepara_vendite_pdv(_vendite())
        result = elabora_riallocazione(cedi, vendite, None, "venduto")
        df = result["allocazioni"]
        if not df.empty:
            assert (df["UM"] == "pezzi").all()

    def test_ceduto_scaduto_produce_avviso(self):
        cedi = prepara_cedi(_cedi(giorni=-1))
        result = elabora_riallocazione(cedi, _ceduto(), None, "ceduto")
        assert result["allocazioni"].empty
        assert any("scaduto" in a.lower() for a in result["avvisi"])

    def test_articolo_senza_storico_usa_fallback(self):
        # ART999 non ha storico, ma ci sono PDV in rotazione_df → deve usare la media
        cedi = prepara_cedi(_cedi(cod="ART999", giorni=10, qta_colli=50))
        ceduto = _ceduto(cod="ART001")  # storico solo per ART001
        result = elabora_riallocazione(cedi, ceduto, None, "ceduto")
        # Con fallback ci deve essere un avviso "nessun storico specifico"
        assert any("nessun storico specifico" in a for a in result["avvisi"])
        # E una proposta di allocazione (non empty)
        assert not result["allocazioni"].empty

    def test_qta_non_supera_disponibile_ceduto(self):
        cedi = prepara_cedi(_cedi(qta_colli=10.0, giorni=10))
        result = elabora_riallocazione(cedi, _ceduto(), None, "ceduto")
        assert result["allocazioni"]["QTA_PROPOSTA"].sum() <= 10

    def test_qta_non_supera_disponibile_venduto(self):
        cedi = prepara_cedi(_cedi(qta_pezzi=10.0, giorni=10))
        vendite = prepara_vendite_pdv(_vendite())
        result = elabora_riallocazione(cedi, vendite, None, "venduto")
        assert result["allocazioni"]["QTA_PROPOSTA"].sum() <= 10

    def test_summary_contiene_campi_attesi(self):
        cedi = prepara_cedi(_cedi())
        result = elabora_riallocazione(cedi, _ceduto(), None, "ceduto")
        s = result["summary"]
        for campo in ("totale_stock", "quantita_a_rischio", "referenze_critiche",
                      "quantita_allocata", "quantita_non_allocata",
                      "n_referenze", "n_pdv_coinvolti"):
            assert campo in s

    def test_pdv_non_attivo_escluso(self):
        cedi = prepara_cedi(_cedi(qta_colli=50, giorni=10))
        ceduto = _ceduto(cod_pdv="PDV01")
        anag = prepara_anagrafica(_anagrafica(cod_pdv="PDV01", attivo=False))
        result = elabora_riallocazione(cedi, ceduto, anag, "ceduto")
        assert result["allocazioni"].empty

    def test_priorita_alta_per_giorni_critici(self):
        cedi = prepara_cedi(_cedi(giorni=3, qta_colli=5))
        result = elabora_riallocazione(cedi, _ceduto(), None, "ceduto")
        df = result["allocazioni"]
        if not df.empty:
            assert (df["PRIORITA"] == "Alta").all()

    def test_sconto_proposto_quando_stock_non_allocato(self):
        # Quantità molto alta rispetto alla capacità → sconto deve essere proposto
        cedi = prepara_cedi(_cedi(qta_colli=1000.0, giorni=2))
        result = elabora_riallocazione(cedi, _ceduto(), None, "ceduto")
        df = result["allocazioni"]
        if not df.empty:
            assert df["SCONTO_PROPOSTO"].notna().any()

    def test_avviso_quantita_non_allocata(self):
        cedi = prepara_cedi(_cedi(qta_colli=1000.0, giorni=2))
        result = elabora_riallocazione(cedi, _ceduto(), None, "ceduto")
        assert any("non allocati" in a for a in result["avvisi"])

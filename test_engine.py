"""
Test per backend/engine.py.
Copre entrambe le modalità (ceduto / venduto), filtri PDV, casi critici e summary.
"""

import pytest
import pandas as pd
from datetime import date, timedelta

from backend.engine import (
    prepara_cedi,
    prepara_ceduto_cedi,
    prepara_vendite_pdv,
    prepara_anagrafica,
    calcola_indice_ceduto,
    calcola_indice_venduto,
    calcola_capacita,
    filtra_pdv,
    assegna_priorita,
    assegna_motivo,
    alloca_quantita,
    elabora_riallocazione,
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

def _cedi(giorni=10, qta=100.0, cod="ART001"):
    return pd.DataFrame([{
        "LOTTO": "L001",
        "COD_ARTICOLO": cod,
        "DESCRIZIONE_ARTICOLO": "Yogurt Bianco",
        "QTA_DISPONIBILE": qta,
        "DATA_SCADENZA": pd.Timestamp(date.today() + timedelta(days=giorni)),
    }])


def _ceduto(cod="ART001", q7=14, q14=28, q30=60, cod_pdv="PDV01", nome="Super A"):
    return pd.DataFrame([{
        "COD_PDV": cod_pdv, "NOME_PDV": nome, "COD_ARTICOLO": cod,
        "QTA_CEDUTA_7GG": q7, "QTA_CEDUTA_14GG": q14, "QTA_CEDUTA_30GG": q30,
    }])


def _vendite(cod="ART001", mese=90, cod_pdv="PDV01", nome="Super A"):
    return pd.DataFrame([{
        "COD_PDV": cod_pdv, "NOME_PDV": nome,
        "COD_ARTICOLO": cod, "QTA_VENDUTA_MESE": mese,
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

    def test_ceduto_colonne_mancanti(self):
        df = pd.DataFrame([{"COD_PDV": "P1"}])
        with pytest.raises(ValueError, match="CEDUTO_CEDI_PDV"):
            prepara_ceduto_cedi(df)

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
# Calcolo indice rotazione
# ---------------------------------------------------------------------------

class TestIndiceRotazione:

    def test_ceduto_formula(self):
        # (14/7)*0.5 + (28/14)*0.3 + (60/30)*0.2 = 1.0 + 0.6 + 0.4 = 2.0
        df = _ceduto(q7=14, q14=28, q30=60)
        result = calcola_indice_ceduto(df)
        assert result["INDICE_ROT"].iloc[0] == pytest.approx(2.0)

    def test_ceduto_unitario(self):
        # (7/7)*0.5 + (14/14)*0.3 + (30/30)*0.2 = 0.5+0.3+0.2 = 1.0
        df = _ceduto(q7=7, q14=14, q30=30)
        result = calcola_indice_ceduto(df)
        assert result["INDICE_ROT"].iloc[0] == pytest.approx(1.0)

    def test_venduto_formula(self):
        df = _vendite(mese=90)
        result = calcola_indice_venduto(df)
        assert result["INDICE_ROT"].iloc[0] == pytest.approx(3.0)  # 90/30

    def test_venduto_zero(self):
        df = _vendite(mese=0)
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
        return pd.DataFrame([{"COD_PDV": "P1", "NOME_PDV": "A", "INDICE_ROT": indice, "CAPACITA_STIMATA": 10}])

    def test_esclude_indice_sotto_soglia(self):
        df = self._pdv_df(SOGLIA_INDICE_MIN - 0.01)
        result = filtra_pdv(df, None)
        assert result.empty

    def test_include_indice_uguale_soglia(self):
        df = self._pdv_df(SOGLIA_INDICE_MIN)
        result = filtra_pdv(df, None)
        assert len(result) == 1

    def test_esclude_pdv_non_attivo(self):
        pdv = self._pdv_df(1.0)
        anag = _anagrafica(cod_pdv="P1", attivo=False)
        result = filtra_pdv(pdv, anag)
        assert result.empty

    def test_include_pdv_attivo(self):
        pdv = self._pdv_df(1.0)
        anag = _anagrafica(cod_pdv="P1", attivo=True)
        result = filtra_pdv(pdv, anag)
        assert len(result) == 1

    def test_anagrafica_none_non_filtra_attivita(self):
        pdv = self._pdv_df(1.0)
        result = filtra_pdv(pdv, None)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# Priorità e motivo
# ---------------------------------------------------------------------------

class TestPrioritaMotivo:

    def test_priorita_alta(self):
        assert assegna_priorita(5) == "Alta"

    def test_priorita_alta_limite(self):
        assert assegna_priorita(1) == "Alta"

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


# ---------------------------------------------------------------------------
# Allocazione quantità
# ---------------------------------------------------------------------------

class TestAllocaQuantita:

    def _pdv(self, cap_list):
        return pd.DataFrame([
            {"COD_PDV": f"P{i}", "NOME_PDV": f"PDV {i}", "CAPACITA_STIMATA": c, "INDICE_ROT": c / 10}
            for i, c in enumerate(cap_list, 1)
        ])

    def test_allocazione_singolo_pdv(self):
        pdv = self._pdv([50.0])
        alloc, non_alloc = alloca_quantita(30.0, pdv, giorni_residui=10)
        assert int(alloc["QTA_PROPOSTA"].sum()) == 30
        assert non_alloc == pytest.approx(0.0)

    def test_quantita_non_allocata(self):
        pdv = self._pdv([10.0])  # capacità max 10
        alloc, non_alloc = alloca_quantita(20.0, pdv, giorni_residui=10)
        assert non_alloc > 0

    def test_max_pdv_normale(self):
        # 15 PDV disponibili, max 10 per modalità normale
        caps = [10.0] * 15
        pdv = self._pdv(caps)
        alloc, _ = alloca_quantita(200.0, pdv, giorni_residui=10)
        assert len(alloc) <= MAX_PDV_NORMALE

    def test_max_pdv_critico(self):
        caps = [10.0] * 10
        pdv = self._pdv(caps)
        alloc, _ = alloca_quantita(200.0, pdv, giorni_residui=GIORNI_CRITICI)
        assert len(alloc) <= MAX_PDV_CRITICO

    def test_non_assegna_meno_di_uno(self):
        # Capacità 0.5: troppo piccola per essere assegnata
        pdv = self._pdv([0.5])
        alloc, _ = alloca_quantita(1.0, pdv, giorni_residui=10)
        assert alloc.empty or (alloc["QTA_PROPOSTA"] >= 1).all()

    def test_ordine_decrescente_capacita(self):
        # Il PDV con capacità maggiore deve ricevere per primo
        pdv = self._pdv([5.0, 30.0, 15.0])
        alloc, _ = alloca_quantita(20.0, pdv, giorni_residui=10)
        assert alloc.iloc[0]["COD_PDV"] == "P2"  # P2 ha capacità 30


# ---------------------------------------------------------------------------
# Integrazione: elabora_riallocazione
# ---------------------------------------------------------------------------

class TestElaboraRiallocazione:

    def test_modalita_ceduto_colonne_output(self):
        cedi = prepara_cedi(_cedi(giorni=10, qta=50))
        ceduto = prepara_ceduto_cedi(_ceduto())
        result = elabora_riallocazione(cedi, ceduto, None, "ceduto")
        df = result["allocazioni"]
        expected = {
            "LOTTO", "COD_ARTICOLO", "DESCRIZIONE_ARTICOLO", "COD_PDV", "NOME_PDV",
            "GIORNI_RESIDUI", "INDICE_ROT", "CAPACITA_STIMATA", "QTA_PROPOSTA",
            "PRIORITA", "MOTIVO", "MODALITA_CALCOLO",
        }
        assert expected == set(df.columns)

    def test_modalita_venduto_colonne_output(self):
        cedi = prepara_cedi(_cedi(giorni=10, qta=50))
        vendite = prepara_vendite_pdv(_vendite())
        result = elabora_riallocazione(cedi, vendite, None, "venduto")
        df = result["allocazioni"]
        assert "MODALITA_CALCOLO" in df.columns
        assert df["MODALITA_CALCOLO"].iloc[0] == "Venduto"

    def test_ceduto_scaduto_produce_avviso(self):
        cedi = prepara_cedi(_cedi(giorni=-1))  # già scaduto
        ceduto = prepara_ceduto_cedi(_ceduto())
        result = elabora_riallocazione(cedi, ceduto, None, "ceduto")
        assert result["allocazioni"].empty
        assert len(result["avvisi"]) == 1
        assert "scaduto" in result["avvisi"][0].lower()

    def test_articolo_senza_storico_produce_avviso(self):
        cedi = prepara_cedi(_cedi(cod="ART999"))
        ceduto = prepara_ceduto_cedi(_ceduto(cod="ART001"))
        result = elabora_riallocazione(cedi, ceduto, None, "ceduto")
        assert result["allocazioni"].empty
        assert len(result["avvisi"]) == 1

    def test_qta_non_supera_disponibile(self):
        cedi = prepara_cedi(_cedi(qta=10.0, giorni=10))
        ceduto = prepara_ceduto_cedi(_ceduto(q7=7, q14=14, q30=30))
        result = elabora_riallocazione(cedi, ceduto, None, "ceduto")
        assert result["allocazioni"]["QTA_PROPOSTA"].sum() <= 10

    def test_summary_contiene_campi_attesi(self):
        cedi = prepara_cedi(_cedi())
        ceduto = prepara_ceduto_cedi(_ceduto())
        result = elabora_riallocazione(cedi, ceduto, None, "ceduto")
        s = result["summary"]
        for campo in ("totale_stock", "quantita_a_rischio", "referenze_critiche",
                      "quantita_allocata", "quantita_non_allocata",
                      "n_referenze", "n_pdv_coinvolti"):
            assert campo in s

    def test_pdv_non_attivo_escluso(self):
        cedi = prepara_cedi(_cedi(qta=50, giorni=10))
        ceduto = prepara_ceduto_cedi(_ceduto(cod_pdv="PDV01"))
        anag = prepara_anagrafica(_anagrafica(cod_pdv="PDV01", attivo=False))
        result = elabora_riallocazione(cedi, ceduto, anag, "ceduto")
        assert result["allocazioni"].empty

    def test_priorita_alta_per_giorni_critici(self):
        cedi = prepara_cedi(_cedi(giorni=3, qta=5))
        ceduto = prepara_ceduto_cedi(_ceduto(q7=7, q14=14, q30=30))
        result = elabora_riallocazione(cedi, ceduto, None, "ceduto")
        df = result["allocazioni"]
        if not df.empty:
            assert (df["PRIORITA"] == "Alta").all()

    def test_avviso_quantita_non_allocata(self):
        # INDICE_ROT = (7/7)*0.5+(14/14)*0.3+(30/30)*0.2 = 1.0
        # CAPACITA_STIMATA = 1.0 * 1 * 0.7 = 0.7 → floor = 0 → non allocato tutto
        # Ma 0.7 < 1 quindi la QTA viene arrotondata a 0 → avviso non allocata
        # Usiamo giorni=2 per avere capacità 1.4 → floor=1 ma con qta=1000 residuo > 0
        cedi = prepara_cedi(_cedi(qta=1000.0, giorni=2))
        ceduto = prepara_ceduto_cedi(_ceduto(q7=7, q14=14, q30=30))
        result = elabora_riallocazione(cedi, ceduto, None, "ceduto")
        avvisi_non_alloc = [a for a in result["avvisi"] if "non allocata" in a]
        assert len(avvisi_non_alloc) == 1

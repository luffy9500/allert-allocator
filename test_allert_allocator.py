"""
Test del motore di riallocazione prodotti in scadenza.
Usa dati sintetici in-memory (nessun file Excel necessario).
"""

import pytest
import pandas as pd
from datetime import date, timedelta
from unittest.mock import patch

from allert_allocator import (
    calcola_indice_rotazione,
    calcola_capacita_stimata,
    alloca_quantita,
    elabora_riallocazione,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_vendite(**overrides):
    """Riga base di vendite PDV."""
    base = {
        "COD_PDV": "PDV01",
        "NOME_PDV": "Supermercato A",
        "COD_ARTICOLO": "ART001",
        "QTA_VENDUTA_7GG": 7.0,
        "QTA_VENDUTA_15GG": 15.0,
        "QTA_VENDUTA_30GG": 30.0,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# calcola_indice_rotazione
# ---------------------------------------------------------------------------

class TestCalcolaIndiceRotazione:

    def test_valori_unitari(self):
        """Con vendite pari al periodo, l'indice deve essere 1.0."""
        df = pd.DataFrame([make_vendite()])
        result = calcola_indice_rotazione(df)
        # (7/7)*0.5 + (15/15)*0.3 + (30/30)*0.2 = 0.5+0.3+0.2 = 1.0
        assert result["INDICE_ROTAZIONE"].iloc[0] == pytest.approx(1.0)

    def test_valori_doppi(self):
        """Vendite doppie rispetto al periodo → indice 2.0."""
        df = pd.DataFrame([make_vendite(QTA_VENDUTA_7GG=14, QTA_VENDUTA_15GG=30, QTA_VENDUTA_30GG=60)])
        result = calcola_indice_rotazione(df)
        assert result["INDICE_ROTAZIONE"].iloc[0] == pytest.approx(2.0)

    def test_zero_vendite(self):
        """Nessuna vendita → indice 0."""
        df = pd.DataFrame([make_vendite(QTA_VENDUTA_7GG=0, QTA_VENDUTA_15GG=0, QTA_VENDUTA_30GG=0)])
        result = calcola_indice_rotazione(df)
        assert result["INDICE_ROTAZIONE"].iloc[0] == pytest.approx(0.0)

    def test_non_modifica_originale(self):
        """La funzione non deve alterare il DataFrame originale."""
        df = pd.DataFrame([make_vendite()])
        _ = calcola_indice_rotazione(df)
        assert "INDICE_ROTAZIONE" not in df.columns


# ---------------------------------------------------------------------------
# calcola_capacita_stimata
# ---------------------------------------------------------------------------

class TestCalcolaCapacitaStimata:

    def test_formula(self):
        """CAPACITA_STIMATA = INDICE_ROTAZIONE * GIORNI_RESIDUI * 0.8"""
        df = pd.DataFrame([{"INDICE_ROTAZIONE": 2.0}])
        result = calcola_capacita_stimata(df, giorni_residui=10)
        assert result["CAPACITA_STIMATA"].iloc[0] == pytest.approx(2.0 * 10 * 0.8)
        assert result["GIORNI_RESIDUI"].iloc[0] == 10

    def test_zero_giorni(self):
        df = pd.DataFrame([{"INDICE_ROTAZIONE": 5.0}])
        result = calcola_capacita_stimata(df, giorni_residui=0)
        assert result["CAPACITA_STIMATA"].iloc[0] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# alloca_quantita
# ---------------------------------------------------------------------------

class TestAllocaQuantita:

    def _make_pdv_df(self, capacita_list):
        return pd.DataFrame([
            {"COD_PDV": f"PDV{i:02d}", "NOME_PDV": f"PDV {i}", "CAPACITA_STIMATA": cap}
            for i, cap in enumerate(capacita_list, start=1)
        ])

    def test_un_pdv_riceve_tutto(self):
        """Un solo PDV con capacità sufficiente riceve tutta la quantità."""
        pdv_df = self._make_pdv_df([100.0])
        result = alloca_quantita(50.0, pdv_df)
        assert len(result) == 1
        assert result["QTA_PROPOSTA"].iloc[0] == pytest.approx(50.0)

    def test_distribuzione_tra_piu_pdv(self):
        """La quantità viene distribuita in ordine decrescente di capacità."""
        # PDV01=20, PDV02=15, PDV03=10 → totale capacità 45, disponibile 45
        pdv_df = self._make_pdv_df([20.0, 15.0, 10.0])
        result = alloca_quantita(45.0, pdv_df)
        # Tutti e tre devono ricevere qualcosa
        assert result["QTA_PROPOSTA"].sum() == pytest.approx(45.0)
        assert len(result) == 3

    def test_pdv_con_zero_capacita_escluso(self):
        """PDV con capacità 0 non compare nell'output."""
        pdv_df = self._make_pdv_df([50.0, 0.0])
        result = alloca_quantita(30.0, pdv_df)
        assert all(result["QTA_PROPOSTA"] > 0)

    def test_quantita_esaurita_prima_di_tutti_i_pdv(self):
        """Se la quantità si esaurisce prima, i PDV restanti non ricevono nulla."""
        pdv_df = self._make_pdv_df([100.0, 100.0, 100.0])
        result = alloca_quantita(50.0, pdv_df)
        assert result["QTA_PROPOSTA"].sum() == pytest.approx(50.0)
        assert len(result) == 1  # solo il primo PDV riceve

    def test_ordine_decrescente_rispettato(self):
        """Il PDV con capacità più alta deve ricevere per primo."""
        # Ordine nei dati: PDV01=10, PDV02=50, PDV03=30
        pdv_df = self._make_pdv_df([10.0, 50.0, 30.0])
        result = alloca_quantita(20.0, pdv_df)
        # PDV02 (capacità 50) deve ricevere tutto
        assert result.iloc[0]["COD_PDV"] == "PDV02"
        assert result["QTA_PROPOSTA"].sum() == pytest.approx(20.0)


# ---------------------------------------------------------------------------
# elabora_riallocazione (integrazione)
# ---------------------------------------------------------------------------

class TestElaboraRiallocazione:

    def _make_cedi_df(self, giorni_scadenza=10, qta=100.0, cod="ART001"):
        return pd.DataFrame([{
            "LOTTO": "L001",
            "COD_ARTICOLO": cod,
            "DESCRIZIONE_ARTICOLO": "Yogurt Bianco",
            "QTA_DISPONIBILE": qta,
            "DATA_SCADENZA": pd.Timestamp(date.today() + timedelta(days=giorni_scadenza)),
        }])

    def _make_vendite_df(self, cod="ART001"):
        return pd.DataFrame([
            make_vendite(COD_PDV="PDV01", NOME_PDV="Super A", COD_ARTICOLO=cod,
                         QTA_VENDUTA_7GG=7, QTA_VENDUTA_15GG=15, QTA_VENDUTA_30GG=30),
            make_vendite(COD_PDV="PDV02", NOME_PDV="Super B", COD_ARTICOLO=cod,
                         QTA_VENDUTA_7GG=14, QTA_VENDUTA_15GG=30, QTA_VENDUTA_30GG=60),
        ])

    def _run(self, cedi_df, vendite_df, tmp_path):
        """Esegue elabora_riallocazione con mock dei file Excel."""
        output_path = str(tmp_path / "output.xlsx")

        with (
            patch("allert_allocator.load_cedi_scadenze", return_value=cedi_df),
            patch("allert_allocator.load_vendite_pdv", return_value=vendite_df),
            patch("pandas.DataFrame.to_excel"),
        ):
            return elabora_riallocazione("fake_cedi.xlsx", "fake_vendite.xlsx", output_path)

    def test_colonne_output(self, tmp_path):
        """Il DataFrame di output deve avere tutte le colonne attese."""
        result = self._run(self._make_cedi_df(), self._make_vendite_df(), tmp_path)
        expected_cols = {
            "LOTTO", "COD_ARTICOLO", "DESCRIZIONE_ARTICOLO",
            "COD_PDV", "NOME_PDV", "GIORNI_RESIDUI",
            "INDICE_ROTAZIONE", "CAPACITA_STIMATA", "QTA_PROPOSTA",
        }
        assert expected_cols == set(result.columns)

    def test_quantita_totale_non_supera_disponibile(self, tmp_path):
        """La somma delle QTA_PROPOSTA non deve mai superare la QTA_DISPONIBILE."""
        qta_disponibile = 50.0
        cedi = self._make_cedi_df(qta=qta_disponibile)
        result = self._run(cedi, self._make_vendite_df(), tmp_path)
        assert float(result["QTA_PROPOSTA"].sum()) <= qta_disponibile + 1e-6

    def test_quantita_interamente_allocata_se_capacita_sufficiente(self, tmp_path):
        """Se la capacità totale dei PDV copre la disponibilità, viene allocato tutto."""
        # PDV con indice 2 e 10 giorni → CAPACITA_STIMATA = 2*10*0.8 = 16 ciascuno → totale 32
        # Disponibile 10 → deve essere allocato tutto
        cedi = self._make_cedi_df(qta=10.0, giorni_scadenza=10)
        result = self._run(cedi, self._make_vendite_df(), tmp_path)
        assert float(result["QTA_PROPOSTA"].sum()) == pytest.approx(10.0)

    def test_prodotto_scaduto_saltato(self, tmp_path):
        """Un prodotto già scaduto (giorni_residui <= 0) non deve generare righe."""
        cedi = self._make_cedi_df(giorni_scadenza=-1)
        result = self._run(cedi, self._make_vendite_df(), tmp_path)
        assert result.empty

    def test_articolo_senza_pdv_saltato(self, tmp_path):
        """Se nessun PDV vende l'articolo, non viene generata alcuna riga."""
        cedi = self._make_cedi_df(cod="ART_SCONOSCIUTO")
        result = self._run(cedi, self._make_vendite_df(cod="ART001"), tmp_path)
        assert result.empty

    def test_giorni_residui_corretti(self, tmp_path):
        """GIORNI_RESIDUI deve corrispondere ai giorni fino alla scadenza."""
        cedi = self._make_cedi_df(giorni_scadenza=7)
        result = self._run(cedi, self._make_vendite_df(), tmp_path)
        assert (result["GIORNI_RESIDUI"] == 7).all()

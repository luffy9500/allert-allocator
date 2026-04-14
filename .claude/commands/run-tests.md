# Run Tests — Allert Allocator

Esegui la suite di test e interpreta i risultati.

## Esecuzione

```bash
# Tutti i test (consigliato)
python -m pytest test_engine.py -v

# Solo un gruppo specifico
python -m pytest test_engine.py::TestElaboraRiallocazione -v
python -m pytest test_engine.py::TestTrasformaCedutoRaw -v
python -m pytest test_engine.py::TestProponiSconto -v
python -m pytest test_engine.py::TestUnisciCeduto -v

# Output breve (solo fallimenti)
python -m pytest test_engine.py -q --tb=short
```

## Gruppi di test

| Classe | # Test | Cosa testa |
|--------|--------|-----------|
| `TestPreparaCedi` | 3 | Validazione file scadenze CEDI |
| `TestPreparaCeduto` | 4 | Validazione file ceduto per periodo |
| `TestCalcolaIndice` | 3 | Formula INDICE_ROT (ceduto + venduto) |
| `TestFiltraPdv` | 4 | Esclusione PDV inattivi o sotto soglia |
| `TestAllocaQuantita` | 5 | Algoritmo greedy con vincoli MAX_PDV |
| `TestProponiSconto` | 9 | 5 tier di sconto per urgenza |
| `TestUnisciCeduto` | 5 | Merge outer di tutti i periodi |
| `TestElaboraRiallocazione` | 12 | Integrazione end-to-end |
| `TestTrasformaCedutoRaw` | 11 | Parsing file grezzo multi-foglio |
| `TestRilevaPeriodoCeduto` | 6 | Rilevamento periodo da nome file |
| `TestSummary` | 5 | Calcolo statistiche summary |
| `TestPriorita` | 4 | Logica priorità Alta/Media/Bassa |

**Totale: 76 test**

## Aggiungere un nuovo test

```python
# In test_engine.py, aggiungi una classe o un metodo:
class TestNuovaFunzionalita:

    def test_caso_base(self):
        # Arrange
        df = pd.DataFrame([{...}])
        # Act
        result = nuova_funzione(df)
        # Assert
        assert result["COLONNA"].iloc[0] == valore_atteso

    def test_caso_limite(self):
        ...
```

## Helper disponibili nei test

```python
_cedi(giorni=10, qta_colli=100, cod="ART001")    # DataFrame CEDI scadenze
_ceduto_7(cod="ART001", q7c=14, cod_pdv="PDV01")  # DataFrame ceduto 7gg
_ceduto_14(...)                                    # DataFrame ceduto 14gg
_ceduto_30(...)                                    # DataFrame ceduto 30gg
_ceduto_60(...)                                    # DataFrame ceduto 60gg
_vendite(cod="ART001", qvc=10, cod_pdv="PDV01")   # DataFrame vendite
_anagrafica(pdv="PDV01", attivo=True)              # DataFrame anagrafica
```

## Interpretare un fallimento

```
FAILED test_engine.py::TestUnisciCeduto::test_articolo_solo_in_60gg_incluso
AssertionError: ART_SOLO_60 deve essere nel merge anche se assente dal 7gg
```

→ Significa che `unisci_ceduto()` ha escluso l'articolo.
→ Controlla che il merge usi `pd.concat(chiavi_frames)` come base, non solo `df_7`.

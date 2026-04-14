# Check Engine — Motore di Allocazione

Analisi e debug del motore di riallocazione (`backend/engine.py`).

## Funzioni principali e dove trovarle

| Funzione | Riga | Descrizione |
|----------|------|-------------|
| `trasforma_ceduto_raw()` | ~61 | Parsing file grezzo multi-foglio |
| `prepara_cedi()` | ~212 | Valida file scadenze CEDI |
| `prepara_ceduto_Xgg()` | ~235 | Valida file ceduto per periodo |
| `unisci_ceduto()` | ~299 | Merge outer tutti i periodi |
| `calcola_indice_ceduto()` | ~371 | Formula INDICE_ROT con pesi temporali |
| `calcola_capacita()` | ~413 | CAPACITA_STIMATA = INDICE_ROT × giorni × coeff |
| `filtra_pdv()` | ~426 | Esclude PDV inattivi e sotto SOGLIA_INDICE_MIN |
| `proponi_sconto()` | ~464 | Suggerisce sconto % per urgenza |
| `alloca_quantita()` | ~501 | Greedy allocation con vincoli MAX_PDV |
| `elabora_riallocazione()` | ~543 | Orchestrazione completa |

## Costanti configurabili

In `backend/engine.py` (modificabili senza rifare il build):

```python
COEFF_CEDUTO = 0.7          # Fattore capacità modalità ceduto
COEFF_VENDUTO = 0.8         # Fattore capacità modalità venduto
SOGLIA_INDICE_MIN = 0.2     # PDV con rotazione < 0.2 esclusi
MAX_PDV_NORMALE = 10        # Max PDV per articolo normale
MAX_PDV_CRITICO = 3         # Max PDV se giorni_residui <= 2
GIORNI_CRITICI = 2          # Soglia urgenza massima
SOGLIA_PRIORITA_ALTA = 5    # Priorità "Alta" se giorni <= 5
SOGLIA_PRIORITA_MEDIA = 15  # Priorità "Media" se giorni <= 15
```

## Formula INDICE_ROT (modalità ceduto)

**Con 60gg disponibile:**
```
INDICE_ROT = (Q7/7)×0.40 + (Q14/14)×0.25 + (Q30/30)×0.20 + (Q60/60)×0.15
```

**Senza 60gg (formula a 3 finestre):**
```
INDICE_ROT = (Q7/7)×0.50 + (Q14/14)×0.30 + (Q30/30)×0.20
```

## Formula CAPACITA_STIMATA

```
CAPACITA_STIMATA = INDICE_ROT × GIORNI_RESIDUI × COEFF
```

Dove `COEFF = 0.7` (ceduto) o `0.8` (venduto).

## Logica sconti

| Giorni residui | Condizione aggiuntiva | Sconto |
|---------------|----------------------|--------|
| ≤ 2 | — | 40% |
| ≤ 5 | — | 25% |
| ≤ 10 | non-allocato > 40% stock | 20% |
| ≤ 15 | non-allocato > 25% stock | 15% |
| ≤ 20 | non-allocato > 15% stock | 10% |
| > 20 o allocato | — | Nessuno |

## Debug un'elaborazione specifica

Per testare un singolo lotto in Python REPL:

```python
import pandas as pd
from datetime import date, timedelta
from backend.engine import elabora_riallocazione, prepara_cedi, prepara_ceduto_7gg, unisci_ceduto

cedi = pd.DataFrame([{
    "LOTTO": "L001", "COD_ARTICOLO": "3026400",
    "DESCRIZIONE_ARTICOLO": "Yogurt", "QTA_DISPONIBILE_COLLI": 50,
    "QTA_DISPONIBILE_PEZZI": 300,
    "DATA_SCADENZA": pd.Timestamp(date.today() + timedelta(days=8))
}])

ceduto7 = pd.DataFrame([{
    "COD_PDV": "20850", "NOME_PDV": "Super A", "COD_ARTICOLO": "3026400",
    "QTA_CEDUTA_7GG_COLLI": 10, "QTA_CEDUTA_7GG_PEZZI": 60
}])

df_cedi = prepara_cedi(cedi)
df_c7 = prepara_ceduto_7gg(ceduto7)
rot = unisci_ceduto(df_c7, None, None)

result = elabora_riallocazione(df_cedi, rot, None, "ceduto")
print(result["allocazioni"])
print(result["avvisi"])
```

## Cosa controllare se un articolo non viene allocato

1. `avvisi` nella risposta → cerca il cod_articolo
2. Possibili cause:
   - `"già scaduto"` → DATA_SCADENZA nel passato
   - `"nessun dato di rotazione"` → articolo non in nessun file ceduto
   - `"nessun PDV idoneo dopo i filtri"` → tutti i PDV sotto SOGLIA o inattivi
   - `"nessun storico specifico"` → solo in 60gg ma non in 7gg → **ora risolto con merge outer**

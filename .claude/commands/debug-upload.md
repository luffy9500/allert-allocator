# Debug Upload File Excel — Allert Allocator

Diagnosi dei problemi più comuni durante l'upload dei file.

## Errori e soluzioni

### "Nessuna riga valida trovata" — file ceduto

Il file viene letto con SheetJS usando indici di colonna **0-based** (non 1-based).
Il mapping corretto è:

| Colonna (1-based) | Indice (0-based) | Campo | Valore atteso |
|-------------------|-----------------|-------|--------------|
| 9 | 8 | Radice articolo | Numero (es. 30264) |
| 10 | 9 | Variante | Numero (es. 0) |
| 12 | 11 | Tipo movimento | Stringa "L" |
| 14 | 13 | Pezzi | Numero |
| 15 | 14 | Imballo | Numero |
| 17 | 16 | Codice PDV | Numero (es. 208500 o 20850) |
| 18 | 17 | Nome PDV | Testo |

**Verifica nel browser (Console DevTools):**
```javascript
// Carica SheetJS e il file per debug
const wb = XLSX.read(await file.arrayBuffer(), {type:'array', raw:true})
const rows = XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]], {header:1})
console.log('Riga 1 (header):', rows[0])
console.log('Riga 2 (dati):', rows[1])
console.log('idx 8:', rows[1][8], '| idx 11:', rows[1][11])
```

### "FUNCTION_PAYLOAD_TOO_LARGE" su Vercel

Il payload JSON supera 4.5 MB anche dopo la riduzione client-side.

**Soluzione:** riduci la dimensione dei chunk in `frontend/src/components/FileUploader.jsx`:
```javascript
// Cambia da 2000 a 1000
const CHUNK_SIZE = 1000
```

### "body stream already read"

Già risolto. Se riappare, verifica che `FileUploader.jsx` usi:
```javascript
const text = await res.text()
let data
try { data = JSON.parse(text) } catch (_) { data = { detail: text } }
```
Non `res.json()` seguito da `res.text()` (il body si può leggere una volta sola).

### Errore 422 "colonne mancanti"

Il file Excel non ha le colonne nominate attese.

**Colonne richieste per tipo:**

| Tipo file | Colonne obbligatorie |
|-----------|---------------------|
| `cedi_scadenze` | LOTTO, COD_ARTICOLO, DESCRIZIONE_ARTICOLO, QTA_DISPONIBILE_COLLI, QTA_DISPONIBILE_PEZZI, DATA_SCADENZA |
| `ceduto_7gg` | COD_PDV, NOME_PDV, COD_ARTICOLO, QTA_CEDUTA_7GG_COLLI, QTA_CEDUTA_7GG_PEZZI |
| `ceduto_30gg` | COD_PDV, NOME_PDV, COD_ARTICOLO, QTA_CEDUTA_30GG_COLLI, QTA_CEDUTA_30GG_PEZZI |
| `vendite_pdv` | COD_PDV, NOME_PDV, COD_ARTICOLO, QTA_VENDUTA_MESE_COLLI, QTA_VENDUTA_MESE_PEZZI |
| `anagrafica_pdv` | COD_PDV, ATTIVO |

### "Sessione non trovata" dopo elaborazione

Su Vercel (serverless) la sessione potrebbe essere persa tra richieste.
I dati sono stati spostati in localStorage. Se l'errore persiste:
1. Ricarica la pagina
2. Ri-carica i file
3. Ri-elabora

### File ceduto con struttura "grezza" (multi-foglio, senza header)

Il sistema riconosce automaticamente il formato grezzo e applica `trasforma_ceduto_raw()`.
Se fallisce entrambi i formati, l'errore riporta la causa specifica.

## Come aggiungere un nuovo tipo file

1. Aggiungi `prepara_nuovotipo()` in `backend/engine.py`
2. Aggiungi entry in `_TIPO_CONFIG` in `backend/router_upload.py`
3. Aggiungi `FileUploader` nel frontend con il tipo corrispondente

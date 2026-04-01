# Allert Allocator — Guida Operativa

> Versione aggiornata al modello con finestre temporali multiple (7/14/30/60gg),
> unità colli/pezzi, fallback articoli senza storico e proposte di sconto.

---

## Indice

1. [Panoramica](#1-panoramica)
2. [Flusso operativo in 4 passi](#2-flusso-operativo-in-4-passi)
3. [Modalità di calcolo](#3-modalità-di-calcolo)
4. [File di input richiesti](#4-file-di-input-richiesti)
5. [Formule di calcolo](#5-formule-di-calcolo)
6. [Fallback articoli senza storico](#6-fallback-articoli-senza-storico)
7. [Proposte di sconto](#7-proposte-di-sconto)
8. [Output — colonne del piano](#8-output--colonne-del-piano)
9. [Regole di priorità e limiti PDV](#9-regole-di-priorità-e-limiti-pdv)
10. [FAQ](#10-faq)

---

## 1. Panoramica

Allert Allocator è uno strumento web che analizza i prodotti in scadenza presenti
al CEDI e calcola automaticamente come redistribuirli ai punti vendita, massimizzando
la quantità smaltita prima della data di scadenza.

**Input**: file Excel estratti dai sistemi gestionali.  
**Output**: file Excel pronto da inviare alla logistica con lotto, PDV, quantità proposta e priorità.

---

## 2. Flusso operativo in 4 passi

```
1. Seleziona modalità  →  2. Carica file  →  3. Elabora  →  4. Esporta Excel
```

| Passo | Dettaglio |
|-------|-----------|
| **1 — Modalità** | Toggle in alto a destra: **Ceduto CEDI** oppure **Venduto PDV** |
| **2 — Upload** | Carica almeno i file obbligatori (*); gli opzionali migliorano l'accuratezza |
| **3 — Elabora** | Clicca "Elabora riallocazione" — l'operazione dura pochi secondi |
| **4 — Esporta** | Clicca "Esporta Excel" per scaricare `piano_operativo.xlsx` |

---

## 3. Modalità di calcolo

### Modalità CEDUTO CEDI
- **Quando usarla**: hai l'estrazione WMS con lo storico di ceduto CEDI → PDV.
- **Unità di misura**: **colli** (sia per le quantità di input che per le assegnazioni proposte).
- **File obbligatori**: `CEDI_SCADENZE` + `CEDUTO_7GG`.
- **File opzionali**: `CEDUTO_14GG`, `CEDUTO_30GG`, `CEDUTO_60GG`, `ANAGRAFICA_PDV`.
- **Coefficiente capacità**: ×0.7 (approccio conservativo).
- **Formula indice** (vedi sezione 5).

### Modalità VENDUTO PDV
- **Quando usarla**: hai il report vendite mensili per articolo dal gestionale del PDV.
- **Unità di misura**: **pezzi** (sia per le quantità di input che per le assegnazioni proposte).
- **File obbligatori**: `CEDI_SCADENZE` + `VENDITE_PDV`.
- **File opzionali**: `ANAGRAFICA_PDV`.
- **Coefficiente capacità**: ×0.8 (approccio leggermente ottimistico).
- **Formula indice** (vedi sezione 5).

> **Nota**: i file di input devono contenere **entrambe** le colonne `_COLLI` e `_PEZZI`
> anche se solo una viene usata in quel run. Il sistema seleziona la colonna corretta
> in base alla modalità attiva.

---

## 4. File di input richiesti

### CEDI_SCADENZE `*` (obbligatorio sempre)

Prodotti in scadenza presenti a magazzino CEDI.

| Colonna | Tipo | Note |
|---------|------|------|
| `LOTTO` | testo/numero | Identificativo lotto |
| `COD_ARTICOLO` | testo/numero | Codice prodotto |
| `DESCRIZIONE_ARTICOLO` | testo | Nome prodotto |
| `QTA_DISPONIBILE_COLLI` | numero | Stock in colli |
| `QTA_DISPONIBILE_PEZZI` | numero | Stock in pezzi |
| `DATA_SCADENZA` | data gg/mm/aaaa | Data di scadenza |

---

### CEDUTO_7GG `*` (obbligatorio in modalità Ceduto)

Ceduto CEDI → PDV negli ultimi **7 giorni**.

| Colonna | Tipo | Note |
|---------|------|------|
| `COD_PDV` | testo/numero | Codice punto vendita |
| `NOME_PDV` | testo | Nome punto vendita |
| `COD_ARTICOLO` | testo/numero | Codice prodotto |
| `QTA_CEDUTA_7GG_COLLI` | numero | Quantità ceduta in colli |
| `QTA_CEDUTA_7GG_PEZZI` | numero | Quantità ceduta in pezzi |

---

### CEDUTO_14GG (opzionale)

Ceduto CEDI → PDV negli ultimi **14 giorni**.

Stessa struttura di CEDUTO_7GG, con colonne:
`QTA_CEDUTA_14GG_COLLI`, `QTA_CEDUTA_14GG_PEZZI`

---

### CEDUTO_30GG (opzionale)

Ceduto CEDI → PDV negli ultimi **30 giorni**.

Colonne: `QTA_CEDUTA_30GG_COLLI`, `QTA_CEDUTA_30GG_PEZZI`

---

### CEDUTO_60GG (opzionale)

Ceduto CEDI → PDV negli ultimi **60 giorni**.

Colonne: `QTA_CEDUTA_60GG_COLLI`, `QTA_CEDUTA_60GG_PEZZI`

> Quando presente, attiva la **formula estesa a 4 finestre** (vedi sezione 5).
> Fornisce una stima più stabile della rotazione per articoli stagionali o a bassa frequenza.

---

### VENDITE_PDV `*` (obbligatorio in modalità Venduto)

Vendite mensili per articolo per PDV.

| Colonna | Tipo | Note |
|---------|------|------|
| `COD_PDV` | testo/numero | Codice punto vendita |
| `NOME_PDV` | testo | Nome punto vendita |
| `COD_ARTICOLO` | testo/numero | Codice prodotto |
| `QTA_VENDUTA_MESE_COLLI` | numero | Vendite mensili in colli |
| `QTA_VENDUTA_MESE_PEZZI` | numero | Vendite mensili in pezzi |

---

### ANAGRAFICA_PDV (opzionale)

Anagrafica punti vendita. Usata per escludere PDV non attivi.

| Colonna | Tipo | Note |
|---------|------|------|
| `COD_PDV` | testo/numero | Codice punto vendita |
| `NOME_PDV` | testo | Nome |
| `CLUSTER_PDV` | testo | Cluster commerciale |
| `FORMATO_PDV` | testo | Formato (super, iper, ecc.) |
| `AREA_GEOGRAFICA` | testo | Area geografica |
| `ATTIVO` | si/no oppure 1/0 | Se no/0 il PDV viene escluso |

---

## 5. Formule di calcolo

### Passo 1 — Giorni residui

```
GIORNI_RESIDUI = DATA_SCADENZA − DATA_ODIERNA
```

I prodotti già scaduti vengono segnalati come avvisi.

---

### Passo 2 — Indice di rotazione PDV

**Modalità Ceduto — formula a 3 finestre** (senza CEDUTO_60GG):

```
INDICE_ROT = (Q7/7)×0.50 + (Q14/14)×0.30 + (Q30/30)×0.20
```

**Modalità Ceduto — formula a 4 finestre** (con CEDUTO_60GG):

```
INDICE_ROT = (Q7/7)×0.40 + (Q14/14)×0.25 + (Q30/30)×0.20 + (Q60/60)×0.15
```

I pesi danno più importanza ai dati recenti.
`Q7`, `Q14`, `Q30`, `Q60` = quantità ceduta nella finestra temporale (in colli).

**Modalità Venduto**:

```
INDICE_ROT = QTA_VENDUTA_MESE / 30
```

Unità: pezzi/giorno.

---

### Passo 3 — Capacità stimata PDV

```
CAPACITA_STIMATA = INDICE_ROT × GIORNI_RESIDUI × COEFF
```

- `COEFF = 0.7` in modalità Ceduto
- `COEFF = 0.8` in modalità Venduto

Rappresenta quante unità quel PDV può assorbire entro la scadenza.

---

### Passo 4 — Filtro PDV

Vengono esclusi:
- PDV con `INDICE_ROT < 0.2` (soglia minima di rotazione)
- PDV con `ATTIVO = no/0` se è presente l'anagrafica

---

### Passo 5 — Assegnazione greedy

I PDV vengono ordinati per capacità decrescente.
Per ogni PDV viene assegnato:

```
QTA_PROPOSTA = min(floor(CAPACITA_STIMATA), stock_residuo)
```

L'assegnazione si ferma quando lo stock è esaurito o si raggiunge il limite PDV.

---

## 6. Fallback articoli senza storico

Se un articolo non ha **nessun dato di storico** (nessuna riga nei file ceduto/vendite),
il sistema **non scarta l'articolo** ma usa una rotazione media come stima.

**Logica fallback**:
1. Calcola `media_per_pdv`: media dell'`INDICE_ROT` per ogni PDV, usando tutti gli altri articoli.
2. Usa quella media come `INDICE_ROT` per l'articolo senza storico.
3. Produce un avviso nel pannello avvisi: `"Articolo XXX: nessun ceduto storico — usata media PDV"`.
4. Nel campo `MOTIVO` dell'output aggiunge il prefisso `"(media PDV)"`.

Questo garantisce che **ogni articolo in scadenza riceva una proposta**, anche i nuovi
introdotti di recente o quelli mai ceduti/venduti nel periodo di riferimento.

---

## 7. Proposte di sconto

Per ogni articolo con quantità **non completamente allocata**, il sistema calcola
uno sconto prezzo suggerito basato sull'urgenza e sulla quota non allocata.

### Logica a soglie

| Condizione | Sconto proposto |
|------------|----------------|
| Giorni residui ≤ 2 | **40%** |
| Giorni residui ≤ 5 | **25%** |
| Giorni residui ≤ 10 e quota non allocata > 50% | **20%** |
| Giorni residui ≤ 7 e quota non allocata > 25% | **15%** |
| Nessuna delle precedenti | `null` (nessuno sconto) |
| Tutto allocato | `null` (nessuno sconto) |

**Quota non allocata** = `QTA_NON_ALLOCATA / QTA_DISPONIBILE`

Lo sconto è presente nella colonna `SCONTO_PROPOSTO` del file di output
e nella visualizzazione nella pagina Referenze.

> Lo sconto è una **proposta operativa**: è l'operatore a decidere se e come applicarlo
> sul sistema di vendita. Il tool non modifica prezzi, genera solo la raccomandazione.

---

## 8. Output — colonne del piano

Il file `piano_operativo.xlsx` contiene una riga per ogni assegnazione LOTTO → PDV.

| Colonna | Descrizione |
|---------|-------------|
| `LOTTO` | Identificativo lotto |
| `COD_ARTICOLO` | Codice prodotto |
| `DESCRIZIONE_ARTICOLO` | Nome prodotto |
| `COD_PDV` | Codice punto vendita assegnatario |
| `NOME_PDV` | Nome punto vendita |
| `GIORNI_RESIDUI` | Giorni alla scadenza al momento dell'elaborazione |
| `INDICE_ROT` | Indice di rotazione calcolato per quel PDV+articolo |
| `CAPACITA_STIMATA` | Stima capacità di assorbimento del PDV |
| `QTA_PROPOSTA` | Quantità da inviare (in colli o pezzi a seconda della modalità) |
| `UM` | Unità di misura: `colli` (ceduto) oppure `pezzi` (venduto) |
| `PRIORITA` | `Alta` / `Media` / `Bassa` (basata sui giorni residui) |
| `MOTIVO` | Motivazione dell'assegnazione (es. "Alta rotazione", "Prodotto critico") |
| `SCONTO_PROPOSTO` | Percentuale sconto suggerita (0.15–0.40) oppure vuoto |

### Priorità

| Valore | Condizione |
|--------|-----------|
| **Alta** | Giorni residui ≤ 5 |
| **Media** | Giorni residui 6–15 |
| **Bassa** | Giorni residui > 15 |

Il piano è ordinato per priorità decrescente (Alta → Media → Bassa).

---

## 9. Regole di priorità e limiti PDV

| Parametro | Valore |
|-----------|--------|
| Max PDV per referenza (normale) | **10** |
| Max PDV per referenza (critica, gg ≤ 2) | **3** |
| Soglia indice minima | **0.2** pz/giorno o colli/giorno |
| Priorità alta | giorni residui ≤ **5** |
| Priorità media | giorni residui ≤ **15** |
| Giorni critici | giorni residui ≤ **2** |

**Perché max 3 PDV per critici?**
Con ≤ 2 giorni residui la logistica ha tempo per una sola consegna urgente;
distribuire su troppi PDV aumenta il rischio di non arrivare in tempo.

---

## 10. FAQ

**Q: Posso caricare solo il CEDUTO_7GG senza gli altri?**  
Sì. Il 7gg è l'unico obbligatorio. Gli altri affinano la stima ma non sono richiesti.

**Q: Cosa succede se carico tutti e 4 i file ceduto?**  
Il sistema usa automaticamente la formula a 4 finestre (40/25/20/15%) che è più
stabile e tiene conto della stagionalità di medio periodo.

**Q: Un PDV è attivo ma non ha mai ricevuto quell'articolo. Viene escluso?**  
Solo se il suo `INDICE_ROT` è sotto 0.2. Se il PDV vende bene altri articoli
simili, il meccanismo di fallback può comunque proporlo (usando la media PDV).

**Q: Come interpreto SCONTO_PROPOSTO = 0.25?**  
Significa che il sistema suggerisce uno sconto del 25% per aumentare la velocità
di sell-through. Applicarlo è una decisione commerciale dell'operatore.

**Q: Posso rielaborare più volte nella stessa sessione?**  
Sì. I file caricati rimangono in memoria per tutta la sessione del browser.
Puoi modificare la modalità e rielaborare senza ricaricare i file.

**Q: La sessione scade?**  
I dati sono in memoria sul server e durano fino al riavvio del servizio.
Per sessioni lunghe è consigliabile ricaricare i file se si notano errori.

**Q: Cosa significa "(media PDV)" nel campo MOTIVO?**  
Indica che l'articolo non aveva storico di ceduto/venduto nel periodo analizzato,
quindi la capacità del PDV è stata stimata usando la rotazione media di tutti
gli altri articoli per quel PDV.

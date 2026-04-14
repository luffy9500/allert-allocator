# Allert Allocator — Setup & Build Guide

> Guida completa per sviluppatori: installazione, sviluppo locale, build desktop Windows, deploy Vercel.

---

## Indice

1. [Struttura del progetto](#1-struttura-del-progetto)
2. [Sviluppo locale](#2-sviluppo-locale)
3. [Build app desktop Windows (.exe)](#3-build-app-desktop-windows-exe)
4. [Deploy web su Vercel](#4-deploy-web-su-vercel)
5. [Architettura tecnica](#5-architettura-tecnica)
6. [Troubleshooting](#6-troubleshooting)
7. [Prompt per Claude — slash command](#7-prompt-per-claude--slash-command)

---

## 1. Struttura del progetto

```
allert-allocator/
│
├── backend/                    ← FastAPI + motore Python
│   ├── main.py                 ← Entry point app (serve anche il frontend React)
│   ├── engine.py               ← Algoritmo di riallocazione
│   ├── session_store.py        ← Storage sessioni in-memory
│   ├── models.py               ← Pydantic models request/response
│   ├── router_upload.py        ← Upload + parsing file Excel
│   ├── router_elabora.py       ← Endpoint /api/elabora
│   └── router_export.py        ← Export Excel risultati
│
├── frontend/                   ← React + Vite SPA
│   ├── src/
│   │   ├── store.js            ← Zustand state (+ localStorage)
│   │   ├── components/
│   │   │   └── FileUploader.jsx  ← Upload SheetJS client-side + chunk JSON
│   │   └── pages/
│   │       ├── Dashboard.jsx
│   │       ├── ElencoReferenze.jsx
│   │       ├── DettaglioReferenza.jsx
│   │       ├── PianoOperativo.jsx
│   │       └── Presentazione.jsx
│   └── dist/                   ← Build React (generata: npm run build)
│
├── desktop/
│   ├── desktop.py              ← Entry point exe (PyWebView + uvicorn)
│   └── desktop.spec            ← Config PyInstaller
│
├── .claude/commands/           ← Slash command per Claude Code/Desktop
│   ├── build-desktop.md
│   ├── debug-upload.md
│   ├── run-tests.md
│   └── check-engine.md
│
├── build_desktop.bat           ← Script build Windows (1 click)
├── requirements.txt            ← Dipendenze Python
├── test_engine.py              ← Test suite (76 test)
├── vercel.json                 ← Config deploy Vercel
├── GUIDA_OPERATIVA.md          ← Guida utente finale
└── SETUP.md                    ← Questo file
```

---

## 2. Sviluppo locale

### Prerequisiti

| Strumento | Versione minima | Note |
|-----------|----------------|------|
| Python    | 3.11+          | `python --version` |
| Node.js   | 18+            | `node --version` |
| pip       | incluso        | |
| npm       | incluso con Node | |

### Installazione

```bash
# 1. Clona il repository
git clone https://github.com/luffy9500/allert-allocator.git
cd allert-allocator

# 2. Dipendenze Python
pip install -r requirements.txt

# 3. Dipendenze Node
cd frontend && npm install && cd ..
```

### Avvio in sviluppo (due terminali)

**Terminale 1 — Backend:**
```bash
uvicorn backend.main:app --reload --port 8000
```

**Terminale 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Accedi a **http://localhost:5173** (Vite proxy → FastAPI su :8000)

### Esegui i test

```bash
python -m pytest test_engine.py -v
```

76 test coprono: motore di allocazione, parsing ceduto raw, calcolo sconti, merge periodi.

---

## 3. Build app desktop Windows (.exe)

### Requisiti

- Windows 10/11 (con WebView2 Runtime — pre-installato)
- Python 3.11+ nel PATH
- Node.js 18+ nel PATH

### Build con un click

Doppio clic su **`build_desktop.bat`** nella root del progetto.

Lo script esegue automaticamente:

| Passo | Comando | Descrizione |
|-------|---------|-------------|
| 1 | `pip install -r requirements.txt` | Installa pywebview, pyinstaller e tutte le deps |
| 2 | `npm install && npm run build` | Compila React in `frontend/dist/` |
| 3 | verifica `frontend/dist/index.html` | Controlla che il build sia riuscito |
| 4 | `pyinstaller desktop\desktop.spec` | Crea l'exe con tutti i file inclusi |
| 5 | verifica `dist\AllertAllocator.exe` | Stampa la dimensione finale |

**Output:** `dist\AllertAllocator.exe` (~100–150 MB)

### Build manuale (step by step)

```bat
:: 1. Compila il frontend
cd frontend
npm install
npm run build
cd ..

:: 2. Installa dipendenze desktop
pip install pywebview>=4.4.1 pyinstaller>=6.6.0

:: 3. Crea l'exe
pyinstaller desktop\desktop.spec --clean --noconfirm
```

### Come funziona l'exe

```
Doppio clic su AllertAllocator.exe
        │
        ├─ Cerca porta libera (preferisce 8765)
        ├─ Avvia FastAPI in thread background
        ├─ Attende health check /api/health (max 15 sec)
        └─ Apre finestra Edge WebView2 → http://127.0.0.1:8765
```

- **Nessun browser esterno** — finestra nativa Windows (Edge WebView2)
- **Nessun limite file** — Python locale, nessun proxy Vercel
- **Sessione stabile** — server resta attivo per tutta la sessione di lavoro
- **Funziona offline** — nessuna connessione internet richiesta

### Distribuzione

Copia `dist\AllertAllocator.exe` su qualsiasi PC Windows 10/11.
Non serve installare Python, Node.js o dipendenze aggiuntive.

> **Nota antivirus:** il file potrebbe essere segnalato come sospetto da alcuni AV
> (comportamento comune con PyInstaller). Aggiungi un'eccezione o usa un certificato
> code-signing aziendale per la distribuzione interna.

---

## 4. Deploy web su Vercel

### Prima volta

```bash
# Installa Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

### `vercel.json` (configurazione attuale)

```json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "rewrites": [
    { "source": "/(.*)", "destination": "/api/index" }
  ]
}
```

### Limitazioni Vercel (versione free)

| Limite | Valore | Impatto |
|--------|--------|---------|
| Payload max request | 4.5 MB | Gestito con chunk upload client-side |
| Timeout funzione | 10 s | Elaborazioni grandi possono essere lente |
| Memoria | 1 GB | Sufficiente per dataset normali |
| Serverless stateless | — | Sessioni in localStorage + risposta completa |

Per dataset molto grandi o uso intensivo, preferire la **versione desktop**.

---

## 5. Architettura tecnica

### Flusso upload file (versione web + desktop)

```
Browser legge file Excel (SheetJS)
    │
    ├─ File ceduto (7/14/30/60gg):
    │   ├─ Parsing posizionale colonne (idx 8,9,11,13,14,16,17)
    │   ├─ Filtra tipo_movimento == "L"
    │   └─ Invia JSON a chunk da 2000 righe → /api/upload/json/{tipo}
    │
    └─ Altri file (scadenze, anagrafica, vendite):
        ├─ Legge colonne nominate da foglio 1
        ├─ Converte date Excel → ISO YYYY-MM-DD
        └─ Invia JSON a chunk da 2000 righe → /api/upload/json/{tipo}
```

### Flusso elaborazione

```
POST /api/elabora  { modalita: "ceduto" | "venduto" }
    │
    ├─ unisci_ceduto(): merge outer di tutti i periodi disponibili
    ├─ calcola_indice_ceduto/venduto(): INDICE_ROT per PDV×Articolo
    ├─ Per ogni lotto (ordinati per scadenza):
    │   ├─ filtra_pdv(): esclude inattivi e INDICE_ROT < 0.2
    │   ├─ calcola_capacita(): INDICE_ROT × giorni × coeff
    │   ├─ sottrai capacità già usata (anti over-assignment)
    │   ├─ alloca_quantita(): greedy per capacità decrescente
    │   └─ proponi_sconto(): 5 tier (≤2d→40%, ≤5d→25%, ≤10d→20%, ≤15d→15%, ≤20d→10%)
    └─ Risposta: summary + allocazioni + referenze_complete (per navigazione offline)
```

### Gestione sessioni

| Ambiente | Metodo | Durata |
|----------|--------|--------|
| Vercel (web) | ID sessione → localStorage + dati in risposta /elabora | Finché localStorage non viene svuotato |
| Desktop (exe) | ID sessione → in-memory (server sempre attivo) | Finché l'exe è aperto |

---

## 6. Troubleshooting

### Upload fallisce con "FUNCTION_PAYLOAD_TOO_LARGE"
**Causa:** file molto grande (>4.5 MB lordi) che SheetJS non comprime abbastanza.  
**Soluzione:** l'upload a chunk è già attivo. Se persiste, ridurre `CHUNK_SIZE` in `FileUploader.jsx` da 2000 a 1000 righe.

### "Nessuna riga valida trovata" su file ceduto
**Causa:** struttura colonne non riconosciuta.  
**Verifica:** nel file grezzo le colonne devono avere (indici 0-based):
- `idx 8` = Radice articolo (numero)
- `idx 11` = Tipo movimento (deve essere `"L"`)
- `idx 13` = Pezzi, `idx 14` = Imballo
- `idx 16` = Cod. PDV, `idx 17` = Nome PDV

### "Sessione non trovata" su Vercel
**Causa:** istanza serverless diversa tra upload e elaborazione.  
**Soluzione:** già risolto — tutti i dati delle referenze vengono restituiti nell'elaborazione e salvati in localStorage.

### L'exe non si apre (WebView2 mancante)
**Causa:** Windows 10 molto vecchio senza aggiornamenti.  
**Soluzione:** scarica WebView2 Runtime da [https://developer.microsoft.com/en-us/microsoft-edge/webview2/](https://developer.microsoft.com/en-us/microsoft-edge/webview2/)

### L'exe viene segnalato dall'antivirus
**Causa:** PyInstaller crea eseguibili che alcuni AV segnalano per euristiche.  
**Soluzione:** aggiungi eccezione per la cartella, oppure usa `--onedir` invece di `--onefile` (meno compresso, meno segnalazioni).

### Build PyInstaller fallisce con ModuleNotFoundError
**Causa:** dipendenza Python non installata.  
**Soluzione:** `pip install -r requirements.txt` poi ritenta.

### Test falliscono
```bash
python -m pytest test_engine.py -v --tb=short
```
Se falliscono, verifica che `pandas`, `openpyxl` siano installati correttamente.

---

## 7. Prompt per Claude — slash command

I file nella cartella `.claude/commands/` sono slash command utilizzabili direttamente
in **Claude Code** (CLI) o **Claude Desktop**.

### Come usarli

**Claude Code (CLI):**
```bash
# Nella root del progetto, digita nel prompt:
/build-desktop
/debug-upload
/run-tests
/check-engine
```

**Claude Desktop:**
1. Copia la cartella `.claude/commands/` in `~/.claude/commands/` sul tuo PC
2. I comandi diventano disponibili globalmente come `/build-desktop`, ecc.

### Lista comandi disponibili

| Comando | Descrizione |
|---------|-------------|
| `/build-desktop` | Guida step-by-step per buildare l'exe Windows |
| `/debug-upload` | Diagnosi problemi upload file Excel |
| `/run-tests` | Esegue la test suite e interpreta i risultati |
| `/check-engine` | Analisi del motore di allocazione |

---

*Generato automaticamente — aggiorna questo file quando cambia l'architettura.*

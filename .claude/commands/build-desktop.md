# Build Desktop Windows — AllertAllocator.exe

Guida step-by-step per creare l'eseguibile Windows standalone.

## Prerequisiti da verificare

Controlla che siano installati:
- Python 3.11+ (`python --version`)
- Node.js 18+ (`node --version`)
- pip funzionante (`pip --version`)

## Passi di build

### 1. Aggiorna il frontend React

```bash
cd frontend
npm install
npm run build
cd ..
```

Verifica che esista `frontend/dist/index.html` dopo il build.

### 2. Installa dipendenze Python (incluse quelle desktop)

```bash
pip install -r requirements.txt
```

Devono essere installati: `pywebview>=4.4.1`, `pyinstaller>=6.6.0`

### 3. Crea l'exe

```bash
pyinstaller desktop/desktop.spec --clean --noconfirm
```

Su Windows usa i backslash:
```bat
pyinstaller desktop\desktop.spec --clean --noconfirm
```

### 4. Verifica output

Il file deve trovarsi in `dist/AllertAllocator.exe` (~100-150 MB).

## In alternativa: script automatico (Windows)

```bat
build_desktop.bat
```

## Test prima di buildare

Per testare senza compilare, dalla root del progetto:

```bash
python desktop/desktop.py
```

Deve aprirsi una finestra nativa con l'app.

## Problemi comuni

**ModuleNotFoundError durante pyinstaller:**
→ Aggiungi il modulo mancante in `hidden_imports` dentro `desktop/desktop.spec`

**Finestra non si apre (WebView2 mancante):**
→ Scarica WebView2 Runtime da Microsoft: https://developer.microsoft.com/microsoft-edge/webview2/

**File segnalato dall'antivirus:**
→ È normale con PyInstaller. Aggiungi eccezione oppure modifica `desktop.spec` con `upx=False` (già impostato).

**Porta 8765 occupata:**
→ Il codice trova automaticamente una porta libera. Non serve intervento manuale.

"""
Entry point per l'applicazione desktop Windows — AllertAllocator.exe

Sequenza di avvio:
  1. Trova una porta TCP libera (preferisce 8765)
  2. Avvia uvicorn + FastAPI in un thread daemon
  3. Polling health check finché il server non risponde
  4. Apre la finestra PyWebView (Edge WebView2, nativo Win10/11)
  5. Alla chiusura della finestra → os._exit(0) termina tutto

Per testare senza compilare:
    cd /path/to/allert-allocator
    python desktop/desktop.py
"""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request

# ── Patch sys.path ────────────────────────────────────────────────────────────
# In bundle PyInstaller: sys._MEIPASS è la root dove i file sono estratti.
# In sviluppo:           il file è in <repo>/desktop/desktop.py → parent è repo root.
if getattr(sys, "frozen", False):
    _ROOT = sys._MEIPASS  # type: ignore[attr-defined]
else:
    _ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ── Import dopo patch ─────────────────────────────────────────────────────────
import uvicorn  # noqa: E402  (import dopo sys.path patch)
import webview  # noqa: E402

from backend.main import app  # noqa: E402

# ── Configurazione ────────────────────────────────────────────────────────────
_PORTA_PREFERITA = 8765
_TITOLO = "Allert Allocator"
_LARGHEZZA = 1400
_ALTEZZA = 860
_MIN_W = 900
_MIN_H = 600


# ── Utilità porta ─────────────────────────────────────────────────────────────

def _trova_porta(preferita: int = _PORTA_PREFERITA) -> int:
    """Restituisce la porta preferita se libera, altrimenti una casuale libera."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("127.0.0.1", preferita))
            return preferita
        except OSError:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]


def _server_gia_attivo(porta: int) -> bool:
    """Controlla se un server Allert Allocator è già in ascolto sulla porta."""
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{porta}/api/health", timeout=1
        ) as resp:
            return resp.status == 200
    except Exception:
        return False


# ── Server ────────────────────────────────────────────────────────────────────

def _avvia_server(porta: int) -> None:
    """Avvia uvicorn in modalità silenziosa. Chiamato in thread daemon."""
    uvicorn.run(app, host="127.0.0.1", port=porta, log_level="error")


def _attendi_server(porta: int, max_sec: float = 15.0) -> bool:
    """
    Polling sull'endpoint /api/health fino a max_sec secondi.
    Restituisce True se il server risponde, False se timeout.
    """
    url = f"http://127.0.0.1:{porta}/api/health"
    scadenza = time.monotonic() + max_sec
    while time.monotonic() < scadenza:
        try:
            with urllib.request.urlopen(url, timeout=1):
                return True
        except Exception:
            time.sleep(0.25)
    return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    # Caso: istanza già in esecuzione sulla porta preferita → riusa il server
    if _server_gia_attivo(_PORTA_PREFERITA):
        porta = _PORTA_PREFERITA
    else:
        porta = _trova_porta(_PORTA_PREFERITA)
        t = threading.Thread(target=_avvia_server, args=(porta,), daemon=True)
        t.start()

        if not _attendi_server(porta):
            # Fallback: mostra errore con tkinter (disponibile su Windows senza deps extra)
            try:
                import tkinter.messagebox as mb  # noqa: PLC0415

                mb.showerror(
                    _TITOLO,
                    "Impossibile avviare il server interno.\n"
                    "Riprova o contatta l'amministratore.",
                )
            except Exception:
                print("ERRORE: server non avviato entro il timeout.", file=sys.stderr)
            sys.exit(1)

    url = f"http://127.0.0.1:{porta}"

    window = webview.create_window(
        _TITOLO,
        url,
        width=_LARGHEZZA,
        height=_ALTEZZA,
        resizable=True,
        min_size=(_MIN_W, _MIN_H),
    )

    # Alla chiusura della finestra termina tutto (incluso il thread daemon uvicorn)
    window.events.closed += lambda: os._exit(0)

    # gui='edgechromium' usa Edge WebView2 (pre-installato su Win10/11)
    # In sviluppo su Linux/Mac usa il backend disponibile (gtk, cocoa, ...)
    try:
        webview.start(gui="edgechromium")
    except Exception:
        webview.start()  # fallback: PyWebView sceglie il backend disponibile


if __name__ == "__main__":
    main()

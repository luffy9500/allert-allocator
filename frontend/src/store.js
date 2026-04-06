/**
 * Zustand store globale.
 *
 * Gestisce:
 *  - modalita:       "ceduto" | "venduto"
 *  - sessionId:      UUID persistente in sessionStorage
 *  - filesCaricati:  quali file sono stati uploadati con successo
 *  - summary:        statistiche di riepilogo dall'ultima elaborazione
 *  - allocazioni:    array di righe AllocazioneRow
 *  - referenze:      array di ReferenzaCompletaRow (per navigazione senza API)
 *  - avvisi:         messaggi di avvertimento
 *  - loading:        true durante le chiamate API
 *  - errore:         stringa di errore, null se nessuno
 *
 * summary, allocazioni, referenze, avvisi sono persistiti in localStorage
 * per sopravvivere al riavvio della sessione server (Vercel serverless).
 */

import { create } from 'zustand'

const LS_KEY = 'allert_risultato'

// Genera o recupera il session ID (sessionStorage = per-tab, non persiste)
function getSessionId() {
  let id = sessionStorage.getItem('allert_session_id')
  if (!id) {
    id = crypto.randomUUID()
    sessionStorage.setItem('allert_session_id', id)
  }
  return id
}

// Carica il risultato precedente da localStorage (se disponibile)
function loadPersistedResult() {
  try {
    const raw = localStorage.getItem(LS_KEY)
    if (raw) return JSON.parse(raw)
  } catch (_) { /* ignore */ }
  return null
}

function saveResult(data) {
  try { localStorage.setItem(LS_KEY, JSON.stringify(data)) } catch (_) { /* ignore */ }
}

const persisted = loadPersistedResult()

const useStore = create((set, get) => ({
  // --- Stato ---
  modalita: 'ceduto',
  sessionId: getSessionId(),
  filesCaricati: {
    cedi_scadenze:  false,
    ceduto_7gg:     false,
    ceduto_14gg:    false,
    ceduto_30gg:    false,
    ceduto_60gg:    false,
    vendite_pdv:    false,
    anagrafica_pdv: false,
  },
  summary:     persisted?.summary     ?? null,
  allocazioni: persisted?.allocazioni ?? [],
  referenze:   persisted?.referenze   ?? [],
  avvisi:      persisted?.avvisi      ?? [],
  loading: false,
  errore: null,

  // --- Azioni ---

  setModalita: (m) => set({ modalita: m }),

  setLoading: (v) => set({ loading: v }),

  setErrore: (e) => set({ errore: e }),

  markFileCaricato: (tipo) =>
    set((s) => ({ filesCaricati: { ...s.filesCaricati, [tipo]: true } })),

  setRisultato: ({ summary, allocazioni, avvisi, referenze = [] }) => {
    saveResult({ summary, allocazioni, avvisi, referenze })
    set({ summary, allocazioni, avvisi, referenze })
  },

  resetRisultato: () => {
    saveResult(null)
    set({ summary: null, allocazioni: [], avvisi: [], referenze: [] })
  },

  // --- Helpers API ---

  apiHeaders: () => ({ 'X-Session-ID': get().sessionId }),
}))

export default useStore

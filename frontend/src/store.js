/**
 * Zustand store globale.
 *
 * Gestisce:
 *  - modalita:       "ceduto" | "venduto"
 *  - sessionId:      UUID persistente in sessionStorage
 *  - filesCaricati:  quali file sono stati uploadati con successo
 *  - summary:        statistiche di riepilogo dall'ultima elaborazione
 *  - allocazioni:    array di righe AllocazioneRow
 *  - avvisi:         messaggi di avvertimento
 *  - loading:        true durante le chiamate API
 *  - errore:         stringa di errore, null se nessuno
 */

import { create } from 'zustand'

// Genera o recupera il session ID
function getSessionId() {
  let id = sessionStorage.getItem('allert_session_id')
  if (!id) {
    id = crypto.randomUUID()
    sessionStorage.setItem('allert_session_id', id)
  }
  return id
}

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
  summary: null,
  allocazioni: [],
  avvisi: [],
  loading: false,
  errore: null,

  // --- Azioni ---

  setModalita: (m) => set({ modalita: m }),

  setLoading: (v) => set({ loading: v }),

  setErrore: (e) => set({ errore: e }),

  markFileCaricato: (tipo) =>
    set((s) => ({ filesCaricati: { ...s.filesCaricati, [tipo]: true } })),

  setRisultato: ({ summary, allocazioni, avvisi }) =>
    set({ summary, allocazioni, avvisi }),

  resetRisultato: () => set({ summary: null, allocazioni: [], avvisi: [] }),

  // --- Helpers API ---

  apiHeaders: () => ({ 'X-Session-ID': get().sessionId }),
}))

export default useStore

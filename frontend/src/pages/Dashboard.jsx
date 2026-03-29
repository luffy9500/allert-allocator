/**
 * Dashboard — pagina principale.
 *
 * Mostra:
 *  - Form di upload dei file Excel
 *  - Pulsante "Elabora"
 *  - KPI cards con le statistiche di riepilogo
 *  - Lista avvisi
 */

import React, { useState } from 'react'
import useStore from '../store.js'
import StatsCard from '../components/StatsCard.jsx'
import FileUploader from '../components/FileUploader.jsx'

const styles = {
  section: { marginBottom: '2rem' },
  h2: { fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', color: '#1a3c6e' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(170px, 1fr))', gap: '1rem' },
  uploadCard: {
    background: '#fff', borderRadius: 8, padding: '1.25rem',
    boxShadow: '0 1px 4px rgba(0,0,0,0.08)', marginBottom: '1rem',
  },
  uploadCols: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem 2rem' },
  btnElabora: {
    padding: '0.6rem 1.8rem', background: '#1a3c6e', color: '#fff',
    border: 'none', borderRadius: 6, fontSize: '0.95rem', fontWeight: 600,
    cursor: 'pointer', marginTop: '0.5rem',
  },
  btnDisabled: { opacity: 0.5, cursor: 'not-allowed' },
  avvisi: {
    background: '#fff3cd', borderLeft: '4px solid #ffc107',
    borderRadius: 4, padding: '0.75rem 1rem', marginTop: '1rem',
  },
  avvisoItem: { fontSize: '0.85rem', marginBottom: '0.25rem' },
  errore: {
    background: '#f8d7da', borderLeft: '4px solid #dc3545',
    borderRadius: 4, padding: '0.75rem 1rem', marginTop: '0.5rem',
    fontSize: '0.88rem',
  },
}

// Definizione upload in base alla modalità
const UPLOAD_COMMON = [
  {
    tipo: 'cedi_scadenze',
    label: 'CEDI_SCADENZE *',
    hint: 'Colonne: LOTTO, COD_ARTICOLO, DESCRIZIONE_ARTICOLO, QTA_DISPONIBILE, DATA_SCADENZA',
  },
  {
    tipo: 'anagrafica_pdv',
    label: 'ANAGRAFICA_PDV (opzionale)',
    hint: 'Colonne: COD_PDV, NOME_PDV, CLUSTER_PDV, FORMATO_PDV, AREA_GEOGRAFICA, ATTIVO',
  },
]
const UPLOAD_CEDUTO = {
  tipo: 'ceduto_cedi',
  label: 'CEDUTO_CEDI_PDV *',
  hint: 'Colonne: COD_PDV, NOME_PDV, COD_ARTICOLO, QTA_CEDUTA_7GG, QTA_CEDUTA_14GG, QTA_CEDUTA_30GG',
}
const UPLOAD_VENDUTO = {
  tipo: 'vendite_pdv',
  label: 'VENDITE_PDV *',
  hint: 'Colonne: COD_PDV, NOME_PDV, COD_ARTICOLO, QTA_VENDUTA_MESE',
}

export default function Dashboard() {
  const {
    modalita, sessionId, apiHeaders,
    filesCaricati, summary, avvisi,
    setRisultato, setLoading, loading, errore, setErrore,
  } = useStore()

  const [localError, setLocalError] = useState(null)

  const rotazioneFile = modalita === 'ceduto' ? UPLOAD_CEDUTO : UPLOAD_VENDUTO

  const canElabora =
    filesCaricati.cedi_scadenze &&
    (modalita === 'ceduto' ? filesCaricati.ceduto_cedi : filesCaricati.vendite_pdv)

  const handleElabora = async () => {
    setLocalError(null)
    setLoading(true)
    try {
      const res = await fetch('/api/elabora', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...apiHeaders() },
        body: JSON.stringify({ modalita }),
      })
      const data = await res.json()
      if (!res.ok) {
        setLocalError(data.detail || 'Errore durante l\'elaborazione')
      } else {
        setRisultato({
          summary: data.summary,
          allocazioni: data.allocazioni,
          avvisi: data.avvisi,
        })
      }
    } catch (err) {
      setLocalError('Errore di rete: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '1.5rem', color: '#1a202c' }}>
        Dashboard
      </h1>

      {/* Upload file */}
      <div style={styles.section}>
        <h2 style={styles.h2}>Carica file</h2>
        <div style={styles.uploadCard}>
          <div style={styles.uploadCols}>
            {UPLOAD_COMMON.map(u => (
              <FileUploader key={u.tipo} {...u} />
            ))}
            <FileUploader {...rotazioneFile} />
          </div>

          <button
            style={{ ...styles.btnElabora, ...((!canElabora || loading) ? styles.btnDisabled : {}) }}
            disabled={!canElabora || loading}
            onClick={handleElabora}
          >
            {loading ? 'Elaborazione…' : 'Elabora riallocazione'}
          </button>

          {localError && <div style={styles.errore}>{localError}</div>}
        </div>
      </div>

      {/* KPI */}
      {summary && (
        <div style={styles.section}>
          <h2 style={styles.h2}>Riepilogo</h2>
          <div style={styles.grid}>
            <StatsCard
              label="Totale stock (unità)"
              value={summary.totale_stock.toLocaleString('it-IT')}
            />
            <StatsCard
              label="Quantità a rischio"
              value={summary.quantita_a_rischio.toLocaleString('it-IT')}
              color="#dc3545"
              sub="giorni residui ≤ 5"
            />
            <StatsCard
              label="Referenze critiche"
              value={summary.referenze_critiche}
              color="#dc3545"
              sub="giorni residui ≤ 2"
            />
            <StatsCard
              label="Quantità allocata"
              value={summary.quantita_allocata.toLocaleString('it-IT')}
              color="#198754"
            />
            <StatsCard
              label="Non allocata"
              value={summary.quantita_non_allocata.toLocaleString('it-IT')}
              color={summary.quantita_non_allocata > 0 ? '#fd7e14' : '#198754'}
            />
            <StatsCard
              label="Referenze totali"
              value={summary.n_referenze}
            />
            <StatsCard
              label="PDV coinvolti"
              value={summary.n_pdv_coinvolti}
            />
          </div>
        </div>
      )}

      {/* Avvisi */}
      {avvisi.length > 0 && (
        <div style={styles.avvisi}>
          <strong style={{ fontSize: '0.88rem' }}>Avvisi ({avvisi.length})</strong>
          {avvisi.map((a, i) => (
            <p key={i} style={styles.avvisoItem}>{a}</p>
          ))}
        </div>
      )}
    </div>
  )
}

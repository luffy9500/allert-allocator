/**
 * Piano Operativo — tabella completa delle assegnazioni con filtri ed export Excel.
 */

import React, { useState, useMemo } from 'react'
import useStore from '../store.js'
import DataTable from '../components/DataTable.jsx'

const COLUMNS = [
  { key: 'lotto',                label: 'Lotto' },
  { key: 'cod_articolo',         label: 'Cod. Art.' },
  { key: 'descrizione_articolo', label: 'Descrizione' },
  { key: 'cod_pdv',              label: 'Cod. PDV' },
  { key: 'nome_pdv',             label: 'Nome PDV' },
  { key: 'giorni_residui',       label: 'GG Res.' },
  { key: 'indice_rot',           label: 'Ind. Rot.', render: v => v?.toFixed(3) },
  { key: 'capacita_stimata',     label: 'Cap. Stim.', render: v => v?.toFixed(1) },
  { key: 'qta_proposta',         label: 'Qta Prop.', render: v => <strong>{v}</strong> },
  { key: 'priorita',             label: 'Priorità' },
  { key: 'motivo',               label: 'Motivo' },
  { key: 'modalita_calcolo',     label: 'Modalità' },
]

const PRIORITA_OPTIONS = ['Tutte', 'Alta', 'Media', 'Bassa']

const styles = {
  toolbar: {
    display: 'flex', gap: '1rem', alignItems: 'center',
    marginBottom: '1rem', flexWrap: 'wrap',
  },
  select: {
    padding: '0.35rem 0.7rem', borderRadius: 4,
    border: '1px solid #dee2e6', fontSize: '0.85rem',
  },
  input: {
    padding: '0.35rem 0.7rem', borderRadius: 4,
    border: '1px solid #dee2e6', fontSize: '0.85rem', width: 180,
  },
  btnExport: {
    padding: '0.4rem 1.2rem', background: '#198754', color: '#fff',
    border: 'none', borderRadius: 4, cursor: 'pointer',
    fontSize: '0.85rem', fontWeight: 600, marginLeft: 'auto',
  },
  btnDisabled: { opacity: 0.5, cursor: 'not-allowed' },
  footer: {
    marginTop: '0.75rem', fontSize: '0.85rem', color: '#495057',
    display: 'flex', gap: '2rem',
  },
  hint: { fontSize: '0.83rem', color: '#6c757d', marginBottom: '1rem' },
}

export default function PianoOperativo() {
  const { allocazioni, apiHeaders } = useStore()
  const [filtroP, setFiltroP] = useState('Tutte')
  const [filtroArt, setFiltroArt] = useState('')
  const [downloading, setDownloading] = useState(false)

  const filtered = useMemo(() => {
    return allocazioni.filter(r => {
      const okP = filtroP === 'Tutte' || r.priorita === filtroP
      const okA = !filtroArt || r.cod_articolo.toLowerCase().includes(filtroArt.toLowerCase()) ||
                  r.descrizione_articolo.toLowerCase().includes(filtroArt.toLowerCase())
      return okP && okA
    })
  }, [allocazioni, filtroP, filtroArt])

  const totaleQta = filtered.reduce((s, r) => s + (r.qta_proposta || 0), 0)

  const handleExport = async () => {
    setDownloading(true)
    try {
      const res = await fetch('/api/export', { headers: apiHeaders() })
      if (!res.ok) {
        alert('Nessun risultato da esportare. Elaborare prima dalla Dashboard.')
        return
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'piano_operativo.xlsx'
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      alert('Errore durante il download: ' + err.message)
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '1.25rem', color: '#1a202c' }}>
        Piano Operativo
      </h1>

      {allocazioni.length === 0 ? (
        <p style={styles.hint}>
          Nessun piano disponibile. Tornare in Dashboard e avviare l'elaborazione.
        </p>
      ) : (
        <>
          <div style={styles.toolbar}>
            <label style={{ fontSize: '0.85rem' }}>
              Priorità:&nbsp;
              <select style={styles.select} value={filtroP} onChange={e => setFiltroP(e.target.value)}>
                {PRIORITA_OPTIONS.map(p => <option key={p}>{p}</option>)}
              </select>
            </label>
            <input
              style={styles.input}
              placeholder="Cerca articolo…"
              value={filtroArt}
              onChange={e => setFiltroArt(e.target.value)}
            />
            <button
              style={{ ...styles.btnExport, ...(downloading ? styles.btnDisabled : {}) }}
              disabled={downloading}
              onClick={handleExport}
            >
              {downloading ? 'Download…' : 'Export Excel'}
            </button>
          </div>

          <DataTable columns={COLUMNS} rows={filtered} />

          <div style={styles.footer}>
            <span><b>{filtered.length}</b> righe visualizzate</span>
            <span>Qta totale proposta: <b>{totaleQta.toLocaleString('it-IT')}</b></span>
          </div>
        </>
      )}
    </div>
  )
}

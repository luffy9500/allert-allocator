import React, { useState, useMemo } from 'react'
import useStore from '../store.js'
import DataTable from '../components/DataTable.jsx'
import InfoTooltip from '../components/InfoTooltip.jsx'

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

export default function PianoOperativo() {
  const { allocazioni, apiHeaders } = useStore()
  const [filtroP, setFiltroP] = useState('Tutte')
  const [filtroArt, setFiltroArt] = useState('')
  const [downloading, setDownloading] = useState(false)

  const filtered = useMemo(() => allocazioni.filter(r => {
    const okP = filtroP === 'Tutte' || r.priorita === filtroP
    const okA = !filtroArt ||
      r.cod_articolo.toLowerCase().includes(filtroArt.toLowerCase()) ||
      r.descrizione_articolo.toLowerCase().includes(filtroArt.toLowerCase())
    return okP && okA
  }), [allocazioni, filtroP, filtroArt])

  const totaleQta = filtered.reduce((s, r) => s + (r.qta_proposta || 0), 0)

  const handleExport = async () => {
    setDownloading(true)
    try {
      const res = await fetch('/api/export', { headers: apiHeaders() })
      if (!res.ok) { alert('Nessun dato da esportare. Elaborare dalla Dashboard.'); return }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = 'piano_operativo.xlsx'; a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      alert('Errore download: ' + err.message)
    } finally {
      setDownloading(false)
    }
  }

  if (allocazioni.length === 0) {
    return (
      <div style={{
        background: '#fff', borderRadius: 10, padding: '3rem 2rem',
        textAlign: 'center', color: '#6c757d',
        boxShadow: '0 1px 6px rgba(0,0,0,0.07)',
      }}>
        <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>📋</div>
        <p style={{ fontWeight: 600, color: '#1a3c6e', marginBottom: '0.4rem' }}>Nessun piano disponibile</p>
        <p style={{ fontSize: '0.88rem' }}>Torna alla <a href="/" style={{ color: '#1a3c6e', fontWeight: 600 }}>Dashboard</a> e avvia l'elaborazione.</p>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
        <h1 style={{ fontSize: '1.3rem', fontWeight: 700, color: '#1a202c', margin: 0 }}>
          Piano Operativo
        </h1>
        <InfoTooltip title="Come leggere il piano">
          <ul style={{ paddingLeft: '1rem', lineHeight: 1.8 }}>
            <li><b>Ind. Rot.:</b> velocità di vendita del PDV</li>
            <li><b>Cap. Stim.:</b> unità che il PDV può assorbire</li>
            <li><b>Qta Prop.:</b> unità da inviare a quel PDV</li>
            <li><b>Motivo:</b> motivazione del ranking</li>
            <li>Clicca l'intestazione di colonna per ordinare</li>
          </ul>
        </InfoTooltip>
      </div>

      {/* Toolbar */}
      <div style={{
        background: '#fff', borderRadius: 8,
        boxShadow: '0 1px 4px rgba(0,0,0,0.07)',
        padding: '0.75rem 1rem',
        display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap',
      }}>
        <label style={{ fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          Priorità:
          <select
            style={{ padding: '0.3rem 0.6rem', borderRadius: 4, border: '1px solid #dee2e6', fontSize: '0.85rem' }}
            value={filtroP}
            onChange={e => setFiltroP(e.target.value)}
          >
            {PRIORITA_OPTIONS.map(p => <option key={p}>{p}</option>)}
          </select>
        </label>

        <input
          style={{ padding: '0.3rem 0.7rem', borderRadius: 4, border: '1px solid #dee2e6', fontSize: '0.85rem', width: 190 }}
          placeholder="🔍 Cerca articolo…"
          value={filtroArt}
          onChange={e => setFiltroArt(e.target.value)}
        />

        {/* Export button */}
        <button
          disabled={downloading}
          onClick={handleExport}
          style={{
            marginLeft: 'auto',
            padding: '0.4rem 1.3rem',
            background: downloading
              ? '#a5d6a7'
              : 'linear-gradient(135deg, #198754, #28a745)',
            color: '#fff', border: 'none', borderRadius: 6,
            fontWeight: 700, cursor: downloading ? 'not-allowed' : 'pointer',
            fontSize: '0.88rem',
            boxShadow: downloading ? 'none' : '0 2px 6px rgba(25,135,84,0.3)',
            transition: 'all 0.15s',
          }}
        >
          {downloading ? '⏳ Download…' : '⬇ Esporta Excel'}
        </button>
      </div>

      {/* Tabella */}
      <DataTable columns={COLUMNS} rows={filtered} />

      {/* Footer */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        fontSize: '0.83rem', color: '#6c757d',
        background: '#fff', borderRadius: 6, padding: '0.6rem 1rem',
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
      }}>
        <span><b style={{ color: '#1a202c' }}>{filtered.length}</b> righe visualizzate</span>
        <span>
          Qta totale proposta:&nbsp;
          <b style={{ color: '#1a3c6e', fontSize: '0.95rem' }}>
            {totaleQta.toLocaleString('it-IT')}
          </b>
        </span>
      </div>
    </div>
  )
}

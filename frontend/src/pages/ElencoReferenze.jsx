import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useStore from '../store.js'
import DataTable from '../components/DataTable.jsx'
import InfoTooltip from '../components/InfoTooltip.jsx'

const COLUMNS = [
  { key: 'cod_articolo',         label: 'Cod. Articolo' },
  { key: 'descrizione_articolo', label: 'Descrizione' },
  { key: 'data_scadenza',        label: 'Scadenza' },
  { key: 'giorni_residui',       label: 'Giorni Residui' },
  { key: 'qta_disponibile',      label: 'Qta Disponibile', render: v => v?.toLocaleString('it-IT') },
  { key: 'n_pdv_idonei',         label: 'PDV Idonei' },
  { key: 'priorita',             label: 'Priorità' },
]

const PRIORITA_OPTIONS = ['Tutte', 'Alta', 'Media', 'Bassa']

export default function ElencoReferenze() {
  const { apiHeaders, summary } = useStore()
  const navigate = useNavigate()
  const [referenze, setReferenze] = useState([])
  const [loading, setLoading] = useState(false)
  const [filtro, setFiltro] = useState('Tutte')
  const [errore, setErrore] = useState(null)

  useEffect(() => {
    setLoading(true)
    setErrore(null)
    fetch('/api/referenze', { headers: apiHeaders() })
      .then(r => {
        if (!r.ok) throw new Error('Elaborare prima i dati dalla Dashboard.')
        return r.json()
      })
      .then(d => setReferenze(d.referenze))
      .catch(e => setErrore(e.message))
      .finally(() => setLoading(false))
  }, [summary])

  const filtered = filtro === 'Tutte' ? referenze : referenze.filter(r => r.priorita === filtro)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
        <h1 style={{ fontSize: '1.3rem', fontWeight: 700, color: '#1a202c', margin: 0 }}>
          Referenze in scadenza
        </h1>
        <InfoTooltip title="Come leggere questa pagina">
          <ul style={{ paddingLeft: '1rem', lineHeight: 1.8 }}>
            <li><b>Giorni Residui:</b> giorni alla scadenza da oggi</li>
            <li><b>PDV Idonei:</b> PDV a cui è stata assegnata la referenza</li>
            <li><b>Priorità Alta:</b> ≤ 5 giorni residui</li>
            <li><b>Priorità Media:</b> ≤ 15 giorni residui</li>
            <li>Clicca una riga per vedere il dettaglio PDV</li>
          </ul>
        </InfoTooltip>
      </div>

      {/* Toolbar */}
      <div style={{
        background: '#fff', borderRadius: 8, padding: '0.75rem 1rem',
        boxShadow: '0 1px 4px rgba(0,0,0,0.07)',
        display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap',
      }}>
        <label style={{ fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          Priorità:
          <select
            style={{ padding: '0.3rem 0.6rem', borderRadius: 4, border: '1px solid #dee2e6', fontSize: '0.85rem' }}
            value={filtro}
            onChange={e => setFiltro(e.target.value)}
          >
            {PRIORITA_OPTIONS.map(p => <option key={p}>{p}</option>)}
          </select>
        </label>
        <span style={{ fontSize: '0.82rem', color: '#6c757d', marginLeft: 'auto' }}>
          {filtered.length} referenz{filtered.length === 1 ? 'a' : 'e'} — clicca per il dettaglio
        </span>
      </div>

      {/* Errore */}
      {errore && (
        <div style={{ background: '#f8d7da', borderLeft: '4px solid #dc3545', borderRadius: 4, padding: '0.7rem 1rem', fontSize: '0.85rem', color: '#721c24' }}>
          {errore} — <a href="/" style={{ color: '#721c24' }}>Torna alla Dashboard</a>
        </div>
      )}

      {loading
        ? <p style={{ color: '#6c757d', fontSize: '0.85rem' }}>Caricamento…</p>
        : <DataTable columns={COLUMNS} rows={filtered} onRowClick={row => navigate(`/referenze/${row.cod_articolo}`)} />
      }
    </div>
  )
}

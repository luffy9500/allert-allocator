/**
 * Elenco Referenze — lista prodotti in scadenza con statistiche sintetiche.
 * Click su una riga → navigazione al dettaglio.
 */

import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useStore from '../store.js'
import DataTable from '../components/DataTable.jsx'

const COLUMNS = [
  { key: 'cod_articolo',        label: 'Cod. Articolo' },
  { key: 'descrizione_articolo', label: 'Descrizione' },
  { key: 'data_scadenza',       label: 'Scadenza' },
  { key: 'giorni_residui',      label: 'Giorni Residui' },
  { key: 'qta_disponibile',     label: 'Qta Disponibile', render: v => v?.toLocaleString('it-IT') },
  { key: 'n_pdv_idonei',        label: 'PDV Idonei' },
  { key: 'priorita',            label: 'Priorità' },
]

const PRIORITA_OPTIONS = ['Tutte', 'Alta', 'Media', 'Bassa']

const styles = {
  toolbar: { display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap' },
  select: {
    padding: '0.35rem 0.7rem', borderRadius: 4,
    border: '1px solid #dee2e6', fontSize: '0.85rem',
  },
  hint: { fontSize: '0.83rem', color: '#6c757d' },
}

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
  }, [summary]) // Aggiorna quando cambia il risultato dell'elaborazione

  const filtered = filtro === 'Tutte'
    ? referenze
    : referenze.filter(r => r.priorita === filtro)

  return (
    <div>
      <h1 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '1.25rem', color: '#1a202c' }}>
        Referenze in scadenza
      </h1>

      <div style={styles.toolbar}>
        <label style={{ fontSize: '0.85rem' }}>
          Priorità:&nbsp;
          <select style={styles.select} value={filtro} onChange={e => setFiltro(e.target.value)}>
            {PRIORITA_OPTIONS.map(p => <option key={p}>{p}</option>)}
          </select>
        </label>
        <span style={styles.hint}>
          {filtered.length} referenz{filtered.length === 1 ? 'a' : 'e'} — clicca per il dettaglio
        </span>
      </div>

      {errore && (
        <p style={{ color: '#dc3545', marginBottom: '1rem', fontSize: '0.88rem' }}>{errore}</p>
      )}

      {loading ? (
        <p style={styles.hint}>Caricamento…</p>
      ) : (
        <DataTable
          columns={COLUMNS}
          rows={filtered}
          onRowClick={row => navigate(`/referenze/${row.cod_articolo}`)}
        />
      )}
    </div>
  )
}

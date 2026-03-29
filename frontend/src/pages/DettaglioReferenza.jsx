/**
 * Dettaglio Referenza — ranking PDV con capacità stimata e quantità proposta.
 */

import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import useStore from '../store.js'
import DataTable from '../components/DataTable.jsx'

const PDV_COLUMNS = [
  { key: 'cod_pdv',         label: 'Cod. PDV' },
  { key: 'nome_pdv',        label: 'Nome PDV' },
  { key: 'indice_rot',      label: 'Indice Rot.', render: v => v?.toFixed(3) },
  { key: 'capacita_stimata', label: 'Cap. Stimata', render: v => v?.toFixed(1) },
  { key: 'qta_proposta',    label: 'Qta Proposta', render: v => <strong>{v}</strong> },
  { key: 'motivo',          label: 'Motivo' },
]

const PRIORITA_COLOR = { Alta: '#dc3545', Media: '#fd7e14', Bassa: '#198754' }

const styles = {
  back: {
    background: 'none', border: 'none', color: '#1a3c6e',
    cursor: 'pointer', fontSize: '0.88rem', marginBottom: '1rem', padding: 0,
  },
  header: {
    background: '#fff', borderRadius: 8, padding: '1.25rem',
    boxShadow: '0 1px 4px rgba(0,0,0,0.08)', marginBottom: '1.5rem',
  },
  h1: { fontSize: '1.3rem', fontWeight: 700, marginBottom: '0.5rem' },
  meta: { display: 'flex', gap: '2rem', fontSize: '0.88rem', color: '#495057', flexWrap: 'wrap' },
  metaItem: {},
  badge: (p) => ({
    display: 'inline-block', padding: '0.2rem 0.7rem',
    borderRadius: 10, fontSize: '0.8rem', fontWeight: 700,
    background: (PRIORITA_COLOR[p] || '#6c757d') + '20',
    color: PRIORITA_COLOR[p] || '#6c757d',
  }),
  hint: { fontSize: '0.83rem', color: '#6c757d' },
}

export default function DettaglioReferenza() {
  const { codArticolo } = useParams()
  const navigate = useNavigate()
  const { apiHeaders } = useStore()
  const [dati, setDati] = useState(null)
  const [loading, setLoading] = useState(true)
  const [errore, setErrore] = useState(null)

  useEffect(() => {
    setLoading(true)
    setErrore(null)
    fetch(`/api/referenze/${encodeURIComponent(codArticolo)}`, { headers: apiHeaders() })
      .then(r => {
        if (!r.ok) return r.json().then(d => { throw new Error(d.detail) })
        return r.json()
      })
      .then(setDati)
      .catch(e => setErrore(e.message))
      .finally(() => setLoading(false))
  }, [codArticolo])

  if (loading) return <p style={styles.hint}>Caricamento…</p>
  if (errore) return <p style={{ color: '#dc3545' }}>{errore}</p>
  if (!dati) return null

  return (
    <div>
      <button style={styles.back} onClick={() => navigate(-1)}>
        ← Torna all'elenco
      </button>

      <div style={styles.header}>
        <h1 style={styles.h1}>{dati.descrizione_articolo}</h1>
        <div style={styles.meta}>
          <span><b>Cod. Articolo:</b> {dati.cod_articolo}</span>
          <span><b>Giorni residui:</b> {dati.giorni_residui}</span>
          <span><b>Qta disponibile:</b> {dati.qta_disponibile?.toLocaleString('it-IT')}</span>
          <span>
            <b>Priorità:</b>{' '}
            <span style={styles.badge(dati.priorita)}>{dati.priorita}</span>
          </span>
        </div>
      </div>

      <h2 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem', color: '#1a3c6e' }}>
        Ranking PDV ({dati.pdv.length} assegnat{dati.pdv.length === 1 ? 'o' : 'i'})
      </h2>

      {dati.pdv.length === 0 ? (
        <p style={styles.hint}>Nessun PDV idoneo per questa referenza.</p>
      ) : (
        <DataTable columns={PDV_COLUMNS} rows={dati.pdv} />
      )}
    </div>
  )
}

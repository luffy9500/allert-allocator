import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useStore from '../store.js'
import InfoTooltip from '../components/InfoTooltip.jsx'

const PRIORITA_OPTIONS = ['Tutte', 'Alta', 'Media', 'Bassa']
const PRIORITA_COLOR = { Alta: '#dc3545', Media: '#fd7e14', Bassa: '#198754' }

export default function ElencoReferenze() {
  const { referenze, summary } = useStore()
  const navigate = useNavigate()
  const [filtro, setFiltro] = useState('Tutte')

  const filtered = filtro === 'Tutte' ? referenze : referenze.filter(r => r.priorita === filtro)

  if (!summary) {
    return (
      <div style={{ background: '#f8d7da', borderLeft: '4px solid #dc3545', borderRadius: 4, padding: '0.7rem 1rem', fontSize: '0.85rem', color: '#721c24' }}>
        Elaborare prima i dati dalla Dashboard. — <a href="/" style={{ color: '#721c24' }}>Torna alla Dashboard</a>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
        <h1 style={{ fontSize: '1.3rem', fontWeight: 700, color: '#1a202c', margin: 0 }}>
          Referenze in scadenza
        </h1>
        <InfoTooltip title="Come leggere questa pagina">
          <ul style={{ paddingLeft: '1rem', lineHeight: 1.8 }}>
            <li><b>Giorni Residui:</b> giorni alla scadenza da oggi (lotto più urgente)</li>
            <li><b>PDV Idonei:</b> punti vendita a cui è stata assegnata la referenza</li>
            <li><b>Qta Allocata:</b> totale unità assegnate ai PDV</li>
            <li><b>Sconto:</b> suggerimento sconto se stock non completamente allocato</li>
            <li><b>Priorità Alta:</b> ≤ 5 giorni residui</li>
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

      {/* Tabella */}
      <div style={{ background: '#fff', borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,0.07)', overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.83rem' }}>
            <thead>
              <tr style={{ background: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
                {['Cod. Articolo', 'Descrizione', 'Scadenza', 'Giorni Res.', 'Qta Disp.', 'Qta Allocata', 'PDV Idonei', 'Sconto', 'Priorità'].map(h => (
                  <th key={h} style={{ padding: '0.6rem 0.85rem', textAlign: 'left', fontWeight: 600, color: '#495057', whiteSpace: 'nowrap' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={9} style={{ padding: '2rem', textAlign: 'center', color: '#6c757d' }}>
                    Nessun dato disponibile.
                  </td>
                </tr>
              ) : filtered.map((row, i) => (
                <tr
                  key={row.cod_articolo}
                  onClick={() => navigate(`/referenze/${row.cod_articolo}`)}
                  style={{
                    background: i % 2 === 0 ? '#fff' : '#f8fafc',
                    cursor: 'pointer',
                    transition: 'background 0.1s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = '#eef2ff'}
                  onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? '#fff' : '#f8fafc'}
                >
                  <td style={{ padding: '0.55rem 0.85rem', fontFamily: 'monospace', fontSize: '0.78rem' }}>{row.cod_articolo}</td>
                  <td style={{ padding: '0.55rem 0.85rem', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{row.descrizione_articolo}</td>
                  <td style={{ padding: '0.55rem 0.85rem', whiteSpace: 'nowrap' }}>{row.data_scadenza}</td>
                  <td style={{ padding: '0.55rem 0.85rem', fontWeight: 700, color: PRIORITA_COLOR[row.priorita] }}>{row.giorni_residui}</td>
                  <td style={{ padding: '0.55rem 0.85rem' }}>{row.qta_disponibile?.toLocaleString('it-IT')}</td>
                  <td style={{ padding: '0.55rem 0.85rem', fontWeight: 600, color: '#198754' }}>{row.qta_allocata?.toLocaleString('it-IT')}</td>
                  <td style={{ padding: '0.55rem 0.85rem' }}>{row.n_pdv_idonei}</td>
                  <td style={{ padding: '0.55rem 0.85rem' }}>
                    {row.sconto_proposto != null
                      ? <span style={{ background: '#fff3cd', color: '#856404', borderRadius: 4, padding: '0.15rem 0.5rem', fontWeight: 700, fontSize: '0.78rem' }}>
                          -{Math.round(row.sconto_proposto * 100)}%
                        </span>
                      : <span style={{ color: '#adb5bd', fontSize: '0.78rem' }}>—</span>
                    }
                  </td>
                  <td style={{ padding: '0.55rem 0.85rem' }}>
                    <span style={{
                      display: 'inline-block', padding: '0.15rem 0.6rem',
                      borderRadius: 10, fontSize: '0.78rem', fontWeight: 700,
                      background: (PRIORITA_COLOR[row.priorita] || '#6c757d') + '22',
                      color: PRIORITA_COLOR[row.priorita] || '#6c757d',
                    }}>{row.priorita}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

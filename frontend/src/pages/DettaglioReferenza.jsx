import React from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import useStore from '../store.js'

const PRIORITA_COLOR = { Alta: '#dc3545', Media: '#fd7e14', Bassa: '#198754' }

export default function DettaglioReferenza() {
  const { codArticolo } = useParams()
  const navigate = useNavigate()
  const { referenze } = useStore()

  const dati = referenze.find(r => r.cod_articolo === codArticolo)

  if (!dati) {
    return (
      <div>
        <button onClick={() => navigate(-1)} style={{ background: 'none', border: 'none', color: '#1a3c6e', cursor: 'pointer', fontSize: '0.88rem', marginBottom: '1rem', padding: 0 }}>
          ← Torna all'elenco
        </button>
        <p style={{ color: '#dc3545', fontSize: '0.88rem' }}>
          Referenza non trovata. <a href="/" style={{ color: '#1a3c6e' }}>Torna alla Dashboard</a> ed elabora prima i dati.
        </p>
      </div>
    )
  }

  const pColor = PRIORITA_COLOR[dati.priorita] || '#6c757d'
  const percentAllocata = dati.qta_disponibile > 0
    ? Math.round((dati.qta_allocata / dati.qta_disponibile) * 100)
    : 0

  return (
    <div>
      <button
        style={{ background: 'none', border: 'none', color: '#1a3c6e', cursor: 'pointer', fontSize: '0.88rem', marginBottom: '1rem', padding: 0 }}
        onClick={() => navigate(-1)}
      >
        ← Torna all'elenco
      </button>

      {/* Header referenza */}
      <div style={{ background: '#fff', borderRadius: 8, padding: '1.25rem', boxShadow: '0 1px 4px rgba(0,0,0,0.08)', marginBottom: '1.25rem' }}>
        <h1 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.65rem', color: '#1a202c' }}>
          {dati.descrizione_articolo}
        </h1>
        <div style={{ display: 'flex', gap: '2rem', fontSize: '0.88rem', color: '#495057', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
          <span><b>Cod. Articolo:</b> {dati.cod_articolo}</span>
          <span><b>Scadenza:</b> {dati.data_scadenza}</span>
          <span><b>Giorni residui:</b> <span style={{ color: pColor, fontWeight: 700 }}>{dati.giorni_residui}</span></span>
          <span>
            <b>Priorità:</b>{' '}
            <span style={{ display: 'inline-block', padding: '0.15rem 0.6rem', borderRadius: 10, fontSize: '0.8rem', fontWeight: 700, background: pColor + '22', color: pColor }}>
              {dati.priorita}
            </span>
          </span>
        </div>

        {/* Barra stock */}
        <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.88rem', color: '#495057', flexWrap: 'wrap', alignItems: 'center' }}>
          <span><b>Qta disponibile:</b> {dati.qta_disponibile?.toLocaleString('it-IT')}</span>
          <span><b>Qta allocata:</b> <span style={{ color: '#198754', fontWeight: 700 }}>{dati.qta_allocata?.toLocaleString('it-IT')}</span></span>
          <span>
            <b>Qta residua:</b>{' '}
            <span style={{ color: (dati.qta_disponibile - dati.qta_allocata) > 0 ? '#dc3545' : '#198754', fontWeight: 700 }}>
              {(dati.qta_disponibile - dati.qta_allocata).toLocaleString('it-IT')}
            </span>
            {' '}({percentAllocata}% allocato)
          </span>
          <span><b>Lotti:</b> {dati.lotti?.join(', ')}</span>
        </div>
        {dati.sconto_proposto != null && (
          <div style={{ marginTop: '0.65rem', background: '#fff3cd', border: '1px solid #ffc107', borderRadius: 6, padding: '0.5rem 0.9rem', display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '1.1rem' }}>💰</span>
            <span style={{ color: '#856404', fontWeight: 700, fontSize: '0.88rem' }}>
              Sconto prezzo suggerito: -{Math.round(dati.sconto_proposto * 100)}%
            </span>
            <span style={{ color: '#856404', fontSize: '0.8rem' }}>
              — {(dati.qta_disponibile - dati.qta_allocata).toLocaleString('it-IT')} unità non allocate
            </span>
          </div>
        )}

        {/* Progress bar allocazione */}
        <div style={{ marginTop: '0.85rem', background: '#e9ecef', borderRadius: 4, height: 8 }}>
          <div style={{
            width: `${Math.min(percentAllocata, 100)}%`, height: '100%',
            background: percentAllocata >= 90 ? '#198754' : percentAllocata >= 50 ? '#fd7e14' : '#dc3545',
            borderRadius: 4, transition: 'width 0.3s',
          }} />
        </div>
      </div>

      {/* Tabella PDV */}
      <h2 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem', color: '#1a3c6e' }}>
        Ranking PDV ({dati.n_pdv_idonei} assegnat{dati.n_pdv_idonei === 1 ? 'o' : 'i'})
      </h2>

      {dati.pdv.length === 0 ? (
        <p style={{ fontSize: '0.83rem', color: '#6c757d' }}>Nessun PDV idoneo per questa referenza.</p>
      ) : (
        <div style={{ background: '#fff', borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,0.07)', overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.83rem' }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
                  {['Lotto', 'Cod. PDV', 'Nome PDV', 'Indice Rot.', 'Cap. Stimata', 'Qta Proposta', 'UM', 'Motivo'].map(h => (
                    <th key={h} style={{ padding: '0.6rem 0.85rem', textAlign: 'left', fontWeight: 600, color: '#495057', whiteSpace: 'nowrap' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {dati.pdv.map((pdv, i) => (
                  <tr key={i} style={{ background: i % 2 === 0 ? '#fff' : '#f8fafc', borderBottom: '1px solid #f0f0f0' }}>
                    <td style={{ padding: '0.5rem 0.85rem', fontFamily: 'monospace', fontSize: '0.78rem', color: '#6c757d' }}>{pdv.lotto}</td>
                    <td style={{ padding: '0.5rem 0.85rem', fontFamily: 'monospace', fontSize: '0.78rem' }}>{pdv.cod_pdv}</td>
                    <td style={{ padding: '0.5rem 0.85rem' }}>{pdv.nome_pdv}</td>
                    <td style={{ padding: '0.5rem 0.85rem', fontFamily: 'monospace' }}>{pdv.indice_rot?.toFixed(3)}</td>
                    <td style={{ padding: '0.5rem 0.85rem', fontFamily: 'monospace' }}>{pdv.capacita_stimata?.toFixed(1)}</td>
                    <td style={{ padding: '0.5rem 0.85rem', fontWeight: 700, color: '#1a3c6e' }}>{pdv.qta_proposta}</td>
                    <td style={{ padding: '0.5rem 0.85rem', fontSize: '0.78rem', color: '#6c757d' }}>{pdv.um}</td>
                    <td style={{ padding: '0.5rem 0.85rem', fontSize: '0.78rem', color: '#495057' }}>{pdv.motivo}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

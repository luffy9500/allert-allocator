import React, { useState } from 'react'
import useStore from '../store.js'
import StatsCard from '../components/StatsCard.jsx'
import FileUploader from '../components/FileUploader.jsx'
import InfoTooltip from '../components/InfoTooltip.jsx'

/* ── Info content per ogni file ── */
const INFO = {
  cedi_scadenze: {
    title: 'CEDI_SCADENZE — Cosa caricare',
    content: (
      <>
        <p>File Excel con i prodotti in scadenza presenti a magazzino CEDI.</p>
        <br />
        <p><b>Colonne obbligatorie:</b></p>
        <ul style={{ paddingLeft: '1rem', marginTop: '0.3rem' }}>
          <li>LOTTO</li>
          <li>COD_ARTICOLO</li>
          <li>DESCRIZIONE_ARTICOLO</li>
          <li>QTA_DISPONIBILE_COLLI</li>
          <li>QTA_DISPONIBILE_PEZZI</li>
          <li>DATA_SCADENZA (gg/mm/aaaa)</li>
        </ul>
      </>
    ),
  },
  anagrafica_pdv: {
    title: 'ANAGRAFICA_PDV — Cosa caricare',
    content: (
      <>
        <p>Anagrafica dei punti vendita. Usata per escludere PDV non attivi.</p>
        <br />
        <p><b>Colonne obbligatorie:</b></p>
        <ul style={{ paddingLeft: '1rem', marginTop: '0.3rem' }}>
          <li>COD_PDV</li>
          <li>NOME_PDV</li>
          <li>CLUSTER_PDV</li>
          <li>FORMATO_PDV</li>
          <li>AREA_GEOGRAFICA</li>
          <li>ATTIVO (si/no oppure 1/0)</li>
        </ul>
      </>
    ),
  },
  ceduto_7gg: {
    title: 'CEDUTO_7GG — Cosa caricare',
    content: (
      <>
        <p>Ceduto CEDI → PDV ultimi <b>7 giorni</b>. <b>Obbligatorio</b> in modalità Ceduto.</p>
        <br />
        <p><b>Colonne obbligatorie:</b></p>
        <ul style={{ paddingLeft: '1rem', marginTop: '0.3rem' }}>
          <li>COD_PDV, NOME_PDV, COD_ARTICOLO</li>
          <li>QTA_CEDUTA_7GG_COLLI</li>
          <li>QTA_CEDUTA_7GG_PEZZI</li>
        </ul>
      </>
    ),
  },
  ceduto_14gg: {
    title: 'CEDUTO_14GG — Cosa caricare',
    content: (
      <>
        <p>Ceduto CEDI → PDV ultimi <b>14 giorni</b>. Opzionale.</p>
        <br />
        <p><b>Colonne obbligatorie:</b></p>
        <ul style={{ paddingLeft: '1rem', marginTop: '0.3rem' }}>
          <li>COD_PDV, NOME_PDV, COD_ARTICOLO</li>
          <li>QTA_CEDUTA_14GG_COLLI</li>
          <li>QTA_CEDUTA_14GG_PEZZI</li>
        </ul>
      </>
    ),
  },
  ceduto_30gg: {
    title: 'CEDUTO_30GG — Cosa caricare',
    content: (
      <>
        <p>Ceduto CEDI → PDV ultimi <b>30 giorni</b>. Opzionale.</p>
        <br />
        <p><b>Colonne obbligatorie:</b></p>
        <ul style={{ paddingLeft: '1rem', marginTop: '0.3rem' }}>
          <li>COD_PDV, NOME_PDV, COD_ARTICOLO</li>
          <li>QTA_CEDUTA_30GG_COLLI</li>
          <li>QTA_CEDUTA_30GG_PEZZI</li>
        </ul>
      </>
    ),
  },
  ceduto_60gg: {
    title: 'CEDUTO_60GG — Cosa caricare',
    content: (
      <>
        <p>Ceduto CEDI → PDV ultimi <b>60 giorni</b>. Opzionale. Quando presente, attiva la formula estesa a 4 finestre temporali.</p>
        <br />
        <p><b>Colonne obbligatorie:</b></p>
        <ul style={{ paddingLeft: '1rem', marginTop: '0.3rem' }}>
          <li>COD_PDV, NOME_PDV, COD_ARTICOLO</li>
          <li>QTA_CEDUTA_60GG_COLLI</li>
          <li>QTA_CEDUTA_60GG_PEZZI</li>
        </ul>
      </>
    ),
  },
  vendite_pdv: {
    title: 'VENDITE_PDV — Cosa caricare',
    content: (
      <>
        <p>Vendite mensili di ogni PDV per articolo.</p>
        <br />
        <p><b>Colonne obbligatorie:</b></p>
        <ul style={{ paddingLeft: '1rem', marginTop: '0.3rem' }}>
          <li>COD_PDV, NOME_PDV, COD_ARTICOLO</li>
          <li>QTA_VENDUTA_MESE_COLLI</li>
          <li>QTA_VENDUTA_MESE_PEZZI</li>
        </ul>
      </>
    ),
  },
}

/* ── Info content per la logica ── */
const INFO_LOGICA_CEDUTO = (
  <>
    <p><b>Formula indice rotazione:</b></p>
    <p style={{ fontFamily: 'monospace', background: 'rgba(255,255,255,0.15)', padding: '0.4rem', borderRadius: 4, margin: '0.4rem 0', fontSize: '0.78rem' }}>
      (Q7gg/7)×0.5 + (Q14gg/14)×0.3 + (Q30gg/30)×0.2
    </p>
    <p><b>Capacità stimata PDV:</b></p>
    <p style={{ fontFamily: 'monospace', background: 'rgba(255,255,255,0.15)', padding: '0.4rem', borderRadius: 4, margin: '0.4rem 0', fontSize: '0.78rem' }}>
      IndiceRot × GiorniResidui × 0.7
    </p>
    <p style={{ marginTop: '0.4rem' }}>Vengono esclusi PDV con indice &lt; 0.2 o non attivi.</p>
  </>
)

const INFO_LOGICA_VENDUTO = (
  <>
    <p><b>Formula indice rotazione:</b></p>
    <p style={{ fontFamily: 'monospace', background: 'rgba(255,255,255,0.15)', padding: '0.4rem', borderRadius: 4, margin: '0.4rem 0', fontSize: '0.78rem' }}>
      QTA_VENDUTA_MESE / 30
    </p>
    <p><b>Capacità stimata PDV:</b></p>
    <p style={{ fontFamily: 'monospace', background: 'rgba(255,255,255,0.15)', padding: '0.4rem', borderRadius: 4, margin: '0.4rem 0', fontSize: '0.78rem' }}>
      IndiceRot × GiorniResidui × 0.8
    </p>
    <p style={{ marginTop: '0.4rem' }}>Vengono esclusi PDV con indice &lt; 0.2 o non attivi.</p>
  </>
)

export default function Dashboard() {
  const {
    modalita, apiHeaders,
    filesCaricati, summary, avvisi,
    setRisultato, setLoading, loading, allocazioni,
  } = useStore()

  const [localError, setLocalError] = useState(null)
  const [downloading, setDownloading] = useState(false)

  const canElabora =
    filesCaricati.cedi_scadenze &&
    (modalita === 'ceduto' ? filesCaricati.ceduto_7gg : filesCaricati.vendite_pdv)

  const hasRisultato = summary !== null && allocazioni.length > 0

  const handleElabora = async () => {
    setLocalError(null)
    setLoading(true)
    try {
      const res = await fetch('/api/elabora', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...apiHeaders() },
        body: JSON.stringify({ modalita }),
      })
      let data
      try { data = await res.json() } catch (_) { data = { detail: await res.text() } }
      if (!res.ok) {
        setLocalError(data.detail || "Errore durante l'elaborazione")
      } else {
        setRisultato({ summary: data.summary, allocazioni: data.allocazioni, avvisi: data.avvisi, referenze: data.referenze ?? [] })
      }
    } catch (err) {
      setLocalError('Errore di rete: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async () => {
    setDownloading(true)
    try {
      const res = await fetch('/api/export', { headers: apiHeaders() })
      if (!res.ok) { alert('Nessun dato da esportare.'); return }
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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

      {/* ── SEZIONE UPLOAD ── */}
      <div style={{
        background: '#fff', borderRadius: 10,
        boxShadow: '0 1px 6px rgba(0,0,0,0.08)', padding: '1.25rem 1.5rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#1a3c6e', margin: 0 }}>
            Carica file di input
          </h2>
          <InfoTooltip title="Come funziona">
            <p>1. Carica almeno i file obbligatori (*)</p>
            <p style={{ marginTop: '0.3rem' }}>2. Seleziona la modalità (Ceduto / Venduto) in alto a destra</p>
            <p style={{ marginTop: '0.3rem' }}>3. Clicca <b>Elabora</b> per calcolare il piano</p>
            <p style={{ marginTop: '0.3rem' }}>4. Esporta il risultato in Excel</p>
          </InfoTooltip>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '0.25rem 2rem' }}>
          <FileUploader
            tipo="cedi_scadenze"
            label="CEDI_SCADENZE"
            obbligatorio
            infoTitle={INFO.cedi_scadenze.title}
            infoContent={INFO.cedi_scadenze.content}
          />
          {modalita === 'ceduto' ? (
            <>
              <FileUploader
                tipo="ceduto_7gg"
                label="CEDUTO 7gg"
                obbligatorio
                infoTitle={INFO.ceduto_7gg.title}
                infoContent={INFO.ceduto_7gg.content}
              />
              <FileUploader
                tipo="ceduto_14gg"
                label="CEDUTO 14gg"
                infoTitle={INFO.ceduto_14gg.title}
                infoContent={INFO.ceduto_14gg.content}
              />
              <FileUploader
                tipo="ceduto_30gg"
                label="CEDUTO 30gg"
                infoTitle={INFO.ceduto_30gg.title}
                infoContent={INFO.ceduto_30gg.content}
              />
              <FileUploader
                tipo="ceduto_60gg"
                label="CEDUTO 60gg"
                infoTitle={INFO.ceduto_60gg.title}
                infoContent={INFO.ceduto_60gg.content}
              />
            </>
          ) : (
            <FileUploader
              tipo="vendite_pdv"
              label="VENDITE_PDV"
              obbligatorio
              infoTitle={INFO.vendite_pdv.title}
              infoContent={INFO.vendite_pdv.content}
            />
          )}
          <FileUploader
            tipo="anagrafica_pdv"
            label="ANAGRAFICA_PDV"
            infoTitle={INFO.anagrafica_pdv.title}
            infoContent={INFO.anagrafica_pdv.content}
          />
        </div>

        {/* Barra azioni */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '1rem', flexWrap: 'wrap' }}>
          <button
            disabled={!canElabora || loading}
            onClick={handleElabora}
            style={{
              padding: '0.55rem 1.8rem',
              background: canElabora && !loading ? 'linear-gradient(135deg,#1a3c6e,#2563ab)' : '#9eb3cc',
              color: '#fff', border: 'none', borderRadius: 6,
              fontSize: '0.95rem', fontWeight: 700,
              cursor: canElabora && !loading ? 'pointer' : 'not-allowed',
              boxShadow: canElabora && !loading ? '0 2px 8px rgba(26,60,110,0.3)' : 'none',
              transition: 'all 0.15s',
            }}
          >
            {loading ? '⏳ Elaborazione…' : '▶ Elabora riallocazione'}
          </button>

          {/* Export — appare solo dopo elaborazione */}
          {hasRisultato && (
            <button
              disabled={downloading}
              onClick={handleExport}
              style={{
                padding: '0.55rem 1.6rem',
                background: downloading ? '#a5d6a7' : 'linear-gradient(135deg,#198754,#28a745)',
                color: '#fff', border: 'none', borderRadius: 6,
                fontSize: '0.95rem', fontWeight: 700,
                cursor: downloading ? 'not-allowed' : 'pointer',
                boxShadow: '0 2px 8px rgba(25,135,84,0.3)',
                transition: 'all 0.15s',
              }}
            >
              {downloading ? '⏳ Download…' : '⬇ Esporta Excel'}
            </button>
          )}

          {!canElabora && (
            <span style={{ fontSize: '0.8rem', color: '#6c757d' }}>
              Carica i file obbligatori (*) per abilitare l'elaborazione
            </span>
          )}
        </div>

        {localError && (
          <div style={{
            background: '#f8d7da', borderLeft: '4px solid #dc3545',
            borderRadius: 4, padding: '0.65rem 1rem', marginTop: '0.75rem',
            fontSize: '0.85rem', color: '#721c24',
          }}>
            {localError}
          </div>
        )}
      </div>

      {/* ── KPI ── */}
      {summary && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#1a3c6e', margin: 0 }}>Riepilogo elaborazione</h2>
            <InfoTooltip title="Cosa significano i valori">
              <ul style={{ paddingLeft: '1rem', lineHeight: 1.7 }}>
                <li><b>A rischio:</b> giorni residui ≤ 5</li>
                <li><b>Critiche:</b> giorni residui ≤ 2</li>
                <li><b>Allocata:</b> quantità assegnata ai PDV</li>
                <li><b>Non allocata:</b> residuo senza PDV idonei</li>
              </ul>
            </InfoTooltip>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(155px, 1fr))', gap: '0.85rem' }}>
            <StatsCard label="Totale stock" value={summary.totale_stock.toLocaleString('it-IT')} sub="unità totali" />
            <StatsCard label="A rischio" value={summary.quantita_a_rischio.toLocaleString('it-IT')} color="#dc3545" sub="gg residui ≤ 5" />
            <StatsCard label="Ref. critiche" value={summary.referenze_critiche} color="#dc3545" sub="gg residui ≤ 2" />
            <StatsCard label="Allocata" value={summary.quantita_allocata.toLocaleString('it-IT')} color="#198754" sub="unità assegnate" />
            <StatsCard
              label="Non allocata"
              value={summary.quantita_non_allocata.toLocaleString('it-IT')}
              color={summary.quantita_non_allocata > 0 ? '#fd7e14' : '#198754'}
              sub="residuo senza PDV"
            />
            <StatsCard label="Referenze" value={summary.n_referenze} sub="articoli elaborati" />
            <StatsCard label="PDV coinvolti" value={summary.n_pdv_coinvolti} sub="punti vendita" />
          </div>
        </div>
      )}

      {/* ── AVVISI ── */}
      {avvisi.length > 0 && (
        <div style={{
          background: '#fff8e1', borderLeft: '4px solid #ffc107',
          borderRadius: 6, padding: '0.85rem 1.1rem',
        }}>
          <div style={{ fontWeight: 700, fontSize: '0.88rem', marginBottom: '0.5rem', color: '#856404' }}>
            ⚠ Avvisi ({avvisi.length})
          </div>
          {avvisi.map((a, i) => (
            <p key={i} style={{ fontSize: '0.83rem', color: '#533f03', marginBottom: '0.2rem' }}>• {a}</p>
          ))}
        </div>
      )}

      {/* ── STATO INIZIALE ── */}
      {!summary && !loading && (
        <div style={{
          background: '#fff', borderRadius: 10,
          boxShadow: '0 1px 6px rgba(0,0,0,0.06)',
          padding: '2.5rem', textAlign: 'center', color: '#6c757d',
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '0.75rem' }}>📊</div>
          <p style={{ fontWeight: 600, fontSize: '1rem', marginBottom: '0.5rem', color: '#1a3c6e' }}>
            Carica i file e avvia l'elaborazione
          </p>
          <p style={{ fontSize: '0.88rem', maxWidth: 400, margin: '0 auto' }}>
            Allert Allocator analizza i prodotti in scadenza e propone automaticamente
            la distribuzione ottimale verso i punti vendita.
          </p>
          <p style={{ fontSize: '0.82rem', marginTop: '0.75rem' }}>
            <a href="/info" style={{ color: '#1a3c6e', fontWeight: 600 }}>
              📋 Scopri come funziona →
            </a>
          </p>
        </div>
      )}
    </div>
  )
}

import React, { useState } from 'react'

const SLIDES = [
  {
    id: 1,
    emoji: '🔔',
    titolo: 'Allert Allocator',
    sottotitolo: 'Riallocazione intelligente dei prodotti in scadenza',
    corpo: (
      <>
        <p style={p}>
          Ogni giorno al CEDI si accumula stock in scadenza che rischia di diventare invenduto.
          <b> Allert Allocator</b> calcola automaticamente dove e quanto distribuire
          ai punti vendita, prima che sia troppo tardi.
        </p>
        <div style={tagRow}>
          {['GDO', 'Logistica', 'Supply Chain', 'Anti-spreco'].map(t => (
            <span key={t} style={tag}>{t}</span>
          ))}
        </div>
      </>
    ),
  },
  {
    id: 2,
    emoji: '⚠️',
    titolo: 'Il problema',
    sottotitolo: 'Stock in scadenza = perdita certa',
    corpo: (
      <div style={grid2}>
        {[
          { icon: '📦', t: 'Stock bloccato a CEDI', d: 'Prodotti con pochi giorni alla scadenza che non vengono smaltiti in tempo' },
          { icon: '🏪', t: 'PDV sottodotati', d: 'Punti vendita ad alta rotazione che potrebbero assorbire facilmente quei prodotti' },
          { icon: '🗑️', t: 'Invenduto evitabile', d: 'Prodotti smaltiti a prezzo ridotto o buttati per mancanza di un piano di distribuzione' },
          { icon: '⏱️', t: 'Decisioni manuali lente', d: 'Analisi fatta a mano su Excel, spesso troppo tardi rispetto alla scadenza' },
        ].map(({ icon, t, d }) => (
          <div key={t} style={card}>
            <div style={{ fontSize: '1.8rem', marginBottom: '0.4rem' }}>{icon}</div>
            <div style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: '0.3rem', color: '#1a3c6e' }}>{t}</div>
            <div style={{ fontSize: '0.82rem', color: '#6c757d' }}>{d}</div>
          </div>
        ))}
      </div>
    ),
  },
  {
    id: 3,
    emoji: '✅',
    titolo: 'La soluzione',
    sottotitolo: 'Un motore di calcolo operativo, usabile ogni giorno',
    corpo: (
      <div style={grid2}>
        {[
          { icon: '📥', t: 'Upload semplice', d: 'Carica i file Excel che già produci (CEDI scadenze + storico vendite/ceduto)' },
          { icon: '🧮', t: 'Calcolo automatico', d: 'Il motore calcola giorni residui, indice di rotazione e capacità di ogni PDV' },
          { icon: '🏆', t: 'Ranking PDV', d: 'Ogni articolo ottiene una lista ordinata dei PDV migliori dove inviarlo' },
          { icon: '📊', t: 'Export operativo', d: 'Un file Excel pronto da inviare alla logistica con lotto, PDV e quantità proposta' },
        ].map(({ icon, t, d }) => (
          <div key={t} style={{ ...card, borderTop: '3px solid #1a3c6e' }}>
            <div style={{ fontSize: '1.8rem', marginBottom: '0.4rem' }}>{icon}</div>
            <div style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: '0.3rem', color: '#1a3c6e' }}>{t}</div>
            <div style={{ fontSize: '0.82rem', color: '#6c757d' }}>{d}</div>
          </div>
        ))}
      </div>
    ),
  },
  {
    id: 4,
    emoji: '🧮',
    titolo: 'Il modello matematico',
    sottotitolo: 'Logica trasparente, nessuna black-box',
    corpo: (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
        {[
          {
            step: '1', label: 'Giorni residui',
            formula: 'DATA_SCADENZA − DATA_ODIERNA',
            note: 'Base di tutto: quanti giorni ha il prodotto prima di scadere',
          },
          {
            step: '2', label: 'Indice di rotazione PDV',
            formula: 'Ceduto: (Q7/7)×0.5 + (Q14/14)×0.3 + (Q30/30)×0.2\nVenduto: QTA_MESE / 30',
            note: 'Velocità di vendita/ceduto del PDV per quell\'articolo',
          },
          {
            step: '3', label: 'Capacità stimata PDV',
            formula: 'IndiceRot × GiorniResidui × 0.7 (ceduto) / 0.8 (venduto)',
            note: 'Quante unità può assorbire quel PDV entro la scadenza',
          },
          {
            step: '4', label: 'Assegnazione greedy',
            formula: 'PDV ordinati per capacità → assegna fino a esaurimento stock',
            note: 'Max 10 PDV per referenza, max 3 se giorni residui ≤ 2',
          },
        ].map(({ step, label, formula, note }) => (
          <div key={step} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
            <div style={{
              width: 28, height: 28, borderRadius: '50%',
              background: '#1a3c6e', color: '#fff',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontWeight: 800, fontSize: '0.85rem', flexShrink: 0,
            }}>{step}</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 700, fontSize: '0.88rem', color: '#1a3c6e' }}>{label}</div>
              <code style={{
                display: 'block', background: '#f0f4f8', padding: '0.35rem 0.6rem',
                borderRadius: 4, fontSize: '0.78rem', margin: '0.25rem 0',
                whiteSpace: 'pre-line', color: '#1a202c',
              }}>{formula}</code>
              <div style={{ fontSize: '0.78rem', color: '#6c757d' }}>{note}</div>
            </div>
          </div>
        ))}
      </div>
    ),
  },
  {
    id: 5,
    emoji: '🔀',
    titolo: 'Due modalità di calcolo',
    sottotitolo: 'Selezionabile con un toggle in alto a destra',
    corpo: (
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        {[
          {
            mode: 'CEDUTO CEDI',
            color: '#1a3c6e',
            icon: '🏭',
            punti: [
              'Usa lo storico di ceduto CEDI → PDV',
              'Finestra temporale 7 / 14 / 30 giorni',
              'Peso maggiore sui dati più recenti (50%)',
              'Coefficiente conservativo: ×0.7',
              'Ideale quando hai l\'estrazione WMS',
            ],
          },
          {
            mode: 'VENDUTO PDV',
            color: '#198754',
            icon: '🛒',
            punti: [
              'Usa le vendite mensili del punto vendita',
              'Un solo dato richiesto: QTA_VENDUTA_MESE',
              'Rotazione = media giornaliera mese',
              'Coefficiente ottimistico: ×0.8',
              'Ideale con report cassieri/gestionale PDV',
            ],
          },
        ].map(({ mode, color, icon, punti }) => (
          <div key={mode} style={{ background: '#fff', borderRadius: 8, padding: '1.1rem', border: `2px solid ${color}` }}>
            <div style={{ fontWeight: 800, color, fontSize: '0.95rem', marginBottom: '0.7rem' }}>
              {icon} {mode}
            </div>
            <ul style={{ paddingLeft: '1.1rem', margin: 0 }}>
              {punti.map(p => (
                <li key={p} style={{ fontSize: '0.82rem', color: '#374151', marginBottom: '0.3rem' }}>{p}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    ),
  },
  {
    id: 6,
    emoji: '📋',
    titolo: 'Output operativo',
    sottotitolo: 'Un file Excel pronto per la logistica',
    corpo: (
      <>
        <p style={{ ...p, marginBottom: '0.9rem' }}>
          Il piano esportato contiene una riga per ogni assegnazione LOTTO → PDV:
        </p>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
            <thead>
              <tr style={{ background: '#1a3c6e', color: '#fff' }}>
                {['LOTTO','COD_ART','PDV','GG_RES','IND_ROT','CAP_STIM','QTA_PROP','PRIORITÀ','MOTIVO'].map(h => (
                  <th key={h} style={{ padding: '0.4rem 0.6rem', textAlign: 'left', whiteSpace: 'nowrap' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                ['L001','YOG001','SUPER-MI-01',4,'1.85','5.2',5,'Alta','Alta rotazione'],
                ['L001','YOG001','SUPER-MI-03',4,'1.20','3.4',3,'Alta','Rotazione standard'],
                ['L002','LAT003','SUPER-TO-02',12,'2.10','25.2',25,'Media','Alta rotazione'],
              ].map((row, i) => (
                <tr key={i} style={{ background: i % 2 === 0 ? '#f8fafc' : '#fff' }}>
                  {row.map((cell, j) => (
                    <td key={j} style={{
                      padding: '0.35rem 0.6rem',
                      color: j === 7 ? (cell === 'Alta' ? '#dc3545' : '#fd7e14') : '#1a202c',
                      fontWeight: j === 6 ? 700 : 400,
                    }}>{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p style={{ fontSize: '0.78rem', color: '#6c757d', marginTop: '0.6rem' }}>
          Ordinamento: Prima Alta priorità → poi Media → poi Bassa. All'interno: capacità stimata decrescente.
        </p>
      </>
    ),
  },
  {
    id: 7,
    emoji: '🚀',
    titolo: 'Come iniziare',
    sottotitolo: 'Operativo in 3 minuti',
    corpo: (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
        {[
          { n: '1', t: 'Prepara i file Excel', d: 'Esporta CEDI_SCADENZE e CEDUTO_CEDI_PDV (o VENDITE_PDV) dai tuoi sistemi gestionali. Servono solo le colonne indicate.' },
          { n: '2', t: 'Seleziona la modalità', d: 'In alto a destra scegli "Ceduto CEDI" se hai lo storico del ceduto, oppure "Venduto PDV" se hai le vendite mensili per punto vendita.' },
          { n: '3', t: 'Carica e Elabora', d: 'Nella Dashboard carica i file e clicca "Elabora riallocazione". In pochi secondi hai il piano completo.' },
          { n: '4', t: 'Esporta e invia', d: 'Clicca "Esporta Excel" per scaricare il piano operativo da inviare alla logistica o ai responsabili PDV.' },
        ].map(({ n, t, d }) => (
          <div key={n} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start', background: '#f8fafc', borderRadius: 8, padding: '0.85rem 1rem' }}>
            <div style={{
              width: 32, height: 32, borderRadius: '50%',
              background: 'linear-gradient(135deg,#1a3c6e,#2563ab)',
              color: '#fff', display: 'flex', alignItems: 'center',
              justifyContent: 'center', fontWeight: 800, fontSize: '0.95rem', flexShrink: 0,
            }}>{n}</div>
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#1a3c6e', marginBottom: '0.25rem' }}>{t}</div>
              <div style={{ fontSize: '0.83rem', color: '#495057' }}>{d}</div>
            </div>
          </div>
        ))}
        <div style={{ textAlign: 'center', marginTop: '0.5rem' }}>
          <a href="/" style={{
            display: 'inline-block', padding: '0.65rem 2rem',
            background: 'linear-gradient(135deg,#1a3c6e,#2563ab)',
            color: '#fff', borderRadius: 8, fontWeight: 700,
            textDecoration: 'none', fontSize: '0.95rem',
            boxShadow: '0 2px 10px rgba(26,60,110,0.3)',
          }}>
            ▶ Vai alla Dashboard
          </a>
        </div>
      </div>
    ),
  },
]

/* ── Stili condivisi ── */
const p = { fontSize: '0.88rem', color: '#374151', lineHeight: 1.6 }
const grid2 = { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '0.85rem' }
const card = { background: '#f8fafc', borderRadius: 8, padding: '1rem', border: '1px solid #e2e8f0' }
const tag = { background: '#dbe8f8', color: '#1a3c6e', borderRadius: 20, padding: '0.2rem 0.7rem', fontSize: '0.78rem', fontWeight: 600 }
const tagRow = { display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.9rem' }

export default function Presentazione() {
  const [slide, setSlide] = useState(0)
  const current = SLIDES[slide]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: 780, margin: '0 auto' }}>

      {/* ── SLIDE CARD ── */}
      <div style={{
        background: '#fff', borderRadius: 12,
        boxShadow: '0 2px 12px rgba(0,0,0,0.09)',
        overflow: 'hidden',
      }}>
        {/* Header slide */}
        <div style={{
          background: 'linear-gradient(135deg, #1a3c6e 0%, #2563ab 100%)',
          padding: '1.5rem 1.75rem',
          color: '#fff',
        }}>
          <div style={{ fontSize: '2.2rem', marginBottom: '0.4rem' }}>{current.emoji}</div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 800, margin: 0 }}>{current.titolo}</h1>
          <p style={{ margin: '0.3rem 0 0', opacity: 0.85, fontSize: '0.9rem' }}>{current.sottotitolo}</p>
          {/* Progress */}
          <div style={{ display: 'flex', gap: '0.3rem', marginTop: '1rem' }}>
            {SLIDES.map((_, i) => (
              <button
                key={i}
                onClick={() => setSlide(i)}
                style={{
                  height: 4, flex: 1, border: 'none', borderRadius: 2,
                  background: i === slide ? '#fff' : 'rgba(255,255,255,0.35)',
                  cursor: 'pointer', padding: 0,
                  transition: 'background 0.2s',
                }}
              />
            ))}
          </div>
        </div>

        {/* Corpo slide */}
        <div style={{ padding: '1.5rem 1.75rem' }}>
          {current.corpo}
        </div>
      </div>

      {/* ── NAVIGAZIONE ── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button
          onClick={() => setSlide(s => Math.max(0, s - 1))}
          disabled={slide === 0}
          style={{
            padding: '0.45rem 1.2rem', borderRadius: 6,
            background: slide === 0 ? '#e2e8f0' : '#fff',
            color: slide === 0 ? '#adb5bd' : '#1a3c6e',
            border: '1.5px solid #dee2e6',
            fontWeight: 600, cursor: slide === 0 ? 'not-allowed' : 'pointer',
            fontSize: '0.88rem',
          }}
        >
          ← Precedente
        </button>

        <span style={{ fontSize: '0.82rem', color: '#6c757d' }}>
          {slide + 1} / {SLIDES.length}
        </span>

        <button
          onClick={() => setSlide(s => Math.min(SLIDES.length - 1, s + 1))}
          disabled={slide === SLIDES.length - 1}
          style={{
            padding: '0.45rem 1.2rem', borderRadius: 6,
            background: slide === SLIDES.length - 1
              ? '#e2e8f0'
              : 'linear-gradient(135deg,#1a3c6e,#2563ab)',
            color: slide === SLIDES.length - 1 ? '#adb5bd' : '#fff',
            border: 'none',
            fontWeight: 600,
            cursor: slide === SLIDES.length - 1 ? 'not-allowed' : 'pointer',
            fontSize: '0.88rem',
            boxShadow: slide === SLIDES.length - 1 ? 'none' : '0 2px 6px rgba(26,60,110,0.25)',
          }}
        >
          Successivo →
        </button>
      </div>

      {/* ── INDICE RAPIDO ── */}
      <div style={{
        background: '#fff', borderRadius: 10, padding: '1rem 1.5rem',
        boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
      }}>
        <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#6c757d', marginBottom: '0.6rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Indice
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
          {SLIDES.map((s, i) => (
            <button
              key={i}
              onClick={() => setSlide(i)}
              style={{
                padding: '0.25rem 0.7rem', borderRadius: 20,
                background: i === slide ? '#1a3c6e' : '#f0f4f8',
                color: i === slide ? '#fff' : '#495057',
                border: 'none', cursor: 'pointer',
                fontSize: '0.78rem', fontWeight: i === slide ? 700 : 400,
                transition: 'all 0.15s',
              }}
            >
              {s.emoji} {s.titolo}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

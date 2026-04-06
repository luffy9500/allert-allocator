import React, { useState } from 'react'

/* ── Stili condivisi — DEVONO stare prima di SLIDES ── */
const p = { fontSize: '0.88rem', color: '#374151', lineHeight: 1.6 }
const grid2 = { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '0.85rem' }
const card = { background: '#f8fafc', borderRadius: 8, padding: '1rem', border: '1px solid #e2e8f0' }
const tag = { background: '#dbe8f8', color: '#1a3c6e', borderRadius: 20, padding: '0.2rem 0.7rem', fontSize: '0.78rem', fontWeight: 600 }
const tagRow = { display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.9rem' }
const code = { display: 'block', background: '#f0f4f8', padding: '0.35rem 0.7rem', borderRadius: 4, fontSize: '0.78rem', fontFamily: 'monospace', margin: '0.3rem 0', whiteSpace: 'pre-line', color: '#1a202c' }
const tbl = { width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }
const th = { background: '#1a3c6e', color: '#fff', padding: '0.4rem 0.7rem', textAlign: 'left', whiteSpace: 'nowrap' }
const td = (i) => ({ padding: '0.35rem 0.7rem', background: i % 2 === 0 ? '#f8fafc' : '#fff', verticalAlign: 'top' })

/* ── Slide helper: step numerato ── */
function Step({ n, label, formula, note }) {
  return (
    <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
      <div style={{
        width: 28, height: 28, borderRadius: '50%', background: '#1a3c6e', color: '#fff',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontWeight: 800, fontSize: '0.85rem', flexShrink: 0,
      }}>{n}</div>
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 700, fontSize: '0.88rem', color: '#1a3c6e' }}>{label}</div>
        {formula && <code style={code}>{formula}</code>}
        {note && <div style={{ fontSize: '0.78rem', color: '#6c757d', marginTop: '0.15rem' }}>{note}</div>}
      </div>
    </div>
  )
}

/* ── Slides ── */
const SLIDES = [
  /* 1 — Intro */
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
        <div style={{ ...grid2, marginTop: '1rem' }}>
          {[
            { icon: '📦', t: 'Problema', d: 'Stock bloccato a CEDI con giorni contati' },
            { icon: '🧮', t: 'Calcolo', d: 'Rotazione × giorni residui → capacità PDV' },
            { icon: '📋', t: 'Piano', d: 'Assegnazione lotto → PDV con quantità e priorità' },
            { icon: '📊', t: 'Export', d: 'File Excel pronto per la logistica' },
          ].map(({ icon, t, d }) => (
            <div key={t} style={{ ...card, borderTop: '3px solid #1a3c6e' }}>
              <div style={{ fontSize: '1.5rem', marginBottom: '0.3rem' }}>{icon}</div>
              <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#1a3c6e' }}>{t}</div>
              <div style={{ fontSize: '0.78rem', color: '#6c757d', marginTop: '0.2rem' }}>{d}</div>
            </div>
          ))}
        </div>
      </>
    ),
  },

  /* 2 — Flusso operativo */
  {
    id: 2,
    emoji: '🚀',
    titolo: 'Come iniziare',
    sottotitolo: 'Operativo in 4 passi',
    corpo: (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {[
          { n: '1', t: 'Seleziona la modalità', d: 'Toggle in alto a destra: Ceduto CEDI oppure Venduto PDV, in base ai dati disponibili.' },
          { n: '2', t: 'Carica i file Excel', d: 'Nella Dashboard carica CEDI_SCADENZE (obbligatorio) + i file storico della modalità scelta. I file opzionali migliorano la precisione.' },
          { n: '3', t: 'Elabora', d: 'Clicca "Elabora riallocazione". Il calcolo dura pochi secondi.' },
          { n: '4', t: 'Esporta e invia', d: 'Clicca "Esporta Excel" per scaricare piano_operativo.xlsx da inviare alla logistica.' },
        ].map(({ n, t, d }) => (
          <div key={n} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start', background: '#f8fafc', borderRadius: 8, padding: '0.85rem 1rem' }}>
            <div style={{
              width: 32, height: 32, borderRadius: '50%',
              background: 'linear-gradient(135deg,#1a3c6e,#2563ab)',
              color: '#fff', display: 'flex', alignItems: 'center',
              justifyContent: 'center', fontWeight: 800, fontSize: '0.95rem', flexShrink: 0,
            }}>{n}</div>
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#1a3c6e', marginBottom: '0.2rem' }}>{t}</div>
              <div style={{ fontSize: '0.83rem', color: '#495057' }}>{d}</div>
            </div>
          </div>
        ))}
        <div style={{ textAlign: 'center', marginTop: '0.25rem' }}>
          <a href="/" style={{
            display: 'inline-block', padding: '0.6rem 2rem',
            background: 'linear-gradient(135deg,#1a3c6e,#2563ab)',
            color: '#fff', borderRadius: 8, fontWeight: 700,
            textDecoration: 'none', fontSize: '0.92rem',
            boxShadow: '0 2px 10px rgba(26,60,110,0.3)',
          }}>▶ Vai alla Dashboard</a>
        </div>
      </div>
    ),
  },

  /* 3 — Modalità di calcolo */
  {
    id: 3,
    emoji: '🔀',
    titolo: 'Due modalità di calcolo',
    sottotitolo: 'Selezionabile con il toggle in alto a destra',
    corpo: (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          {[
            {
              mode: 'CEDUTO CEDI', color: '#1a3c6e', icon: '🏭',
              punti: [
                'Storico ceduto CEDI → PDV (7/14/30/60gg)',
                'Unità: COLLI',
                'Formula pesata con pesi decrescenti nel tempo',
                'Coefficiente conservativo ×0.7',
                'Ideale con estrazione WMS',
              ],
            },
            {
              mode: 'VENDUTO PDV', color: '#198754', icon: '🛒',
              punti: [
                'Vendite mensili per articolo per PDV',
                'Unità: PEZZI',
                'Rotazione = media giornaliera del mese',
                'Coefficiente ottimistico ×0.8',
                'Ideale con report gestionale PDV',
              ],
            },
          ].map(({ mode, color, icon, punti }) => (
            <div key={mode} style={{ background: '#fff', borderRadius: 8, padding: '1rem', border: `2px solid ${color}` }}>
              <div style={{ fontWeight: 800, color, fontSize: '0.9rem', marginBottom: '0.6rem' }}>{icon} {mode}</div>
              <ul style={{ paddingLeft: '1.1rem', margin: 0 }}>
                {punti.map(pt => <li key={pt} style={{ fontSize: '0.82rem', color: '#374151', marginBottom: '0.25rem' }}>{pt}</li>)}
              </ul>
            </div>
          ))}
        </div>
        <div style={{ background: '#fff8e1', borderRadius: 8, padding: '0.85rem 1rem', fontSize: '0.82rem', color: '#856404' }}>
          <b>Nota:</b> i file devono contenere <b>entrambe</b> le colonne <code style={{ background: 'rgba(0,0,0,0.07)', padding: '0.1rem 0.3rem', borderRadius: 3 }}>_COLLI</code> e <code style={{ background: 'rgba(0,0,0,0.07)', padding: '0.1rem 0.3rem', borderRadius: 3 }}>_PEZZI</code>.
          Il sistema seleziona automaticamente quella corretta in base alla modalità attiva.
        </div>
      </div>
    ),
  },

  /* 4 — File di input */
  {
    id: 4,
    emoji: '📥',
    titolo: 'File di input richiesti',
    sottotitolo: '* = obbligatorio, gli altri migliorano la precisione',
    corpo: (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', fontSize: '0.82rem' }}>
        {[
          {
            nome: 'CEDI_SCADENZE *', color: '#1a3c6e', sempre: true,
            colonne: 'LOTTO · COD_ARTICOLO · DESCRIZIONE_ARTICOLO · QTA_DISPONIBILE_COLLI · QTA_DISPONIBILE_PEZZI · DATA_SCADENZA',
            note: 'Obbligatorio sempre. Contiene i prodotti in scadenza al CEDI.',
          },
          {
            nome: 'CEDUTO_7GG *', color: '#1a3c6e',
            colonne: 'COD_PDV · NOME_PDV · COD_ARTICOLO · QTA_CEDUTA_7GG_COLLI · QTA_CEDUTA_7GG_PEZZI',
            note: 'Obbligatorio in modalità Ceduto. Ceduto CEDI→PDV ultimi 7 giorni.',
          },
          {
            nome: 'CEDUTO_14GG', color: '#6c757d',
            colonne: 'COD_PDV · NOME_PDV · COD_ARTICOLO · QTA_CEDUTA_14GG_COLLI · QTA_CEDUTA_14GG_PEZZI',
            note: 'Opzionale. Affina la stima di rotazione.',
          },
          {
            nome: 'CEDUTO_30GG', color: '#6c757d',
            colonne: 'COD_PDV · NOME_PDV · COD_ARTICOLO · QTA_CEDUTA_30GG_COLLI · QTA_CEDUTA_30GG_PEZZI',
            note: 'Opzionale.',
          },
          {
            nome: 'CEDUTO_60GG', color: '#fd7e14',
            colonne: 'COD_PDV · NOME_PDV · COD_ARTICOLO · QTA_CEDUTA_60GG_COLLI · QTA_CEDUTA_60GG_PEZZI',
            note: 'Opzionale. Attiva formula a 4 finestre (più stabile per articoli stagionali).',
          },
          {
            nome: 'VENDITE_PDV *', color: '#198754',
            colonne: 'COD_PDV · NOME_PDV · COD_ARTICOLO · QTA_VENDUTA_MESE_COLLI · QTA_VENDUTA_MESE_PEZZI',
            note: 'Obbligatorio in modalità Venduto.',
          },
          {
            nome: 'ANAGRAFICA_PDV', color: '#6c757d',
            colonne: 'COD_PDV · NOME_PDV · CLUSTER_PDV · FORMATO_PDV · AREA_GEOGRAFICA · ATTIVO',
            note: 'Opzionale. Esclude PDV non attivi (ATTIVO = no/0).',
          },
        ].map(({ nome, color, colonne, note }) => (
          <div key={nome} style={{ background: '#f8fafc', borderRadius: 6, padding: '0.6rem 0.85rem', borderLeft: `3px solid ${color}` }}>
            <div style={{ fontWeight: 700, color, marginBottom: '0.2rem' }}>{nome}</div>
            <div style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: '#374151', marginBottom: '0.15rem' }}>{colonne}</div>
            <div style={{ color: '#6c757d', fontSize: '0.77rem' }}>{note}</div>
          </div>
        ))}
      </div>
    ),
  },

  /* 5 — Modello matematico */
  {
    id: 5,
    emoji: '🧮',
    titolo: 'Il modello matematico',
    sottotitolo: 'Logica trasparente, nessuna black-box',
    corpo: (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
        <Step n="1" label="Giorni residui"
          formula="GIORNI_RESIDUI = DATA_SCADENZA − DATA_ODIERNA"
          note="Prodotti già scaduti generano un avviso ma non vengono esclusi automaticamente." />
        <Step n="2" label="Indice di rotazione PDV (modalità Ceduto)"
          formula={
            "Formula 3 finestre (senza 60gg):\n  (Q7/7)×0.50 + (Q14/14)×0.30 + (Q30/30)×0.20\n\nFormula 4 finestre (con 60gg):\n  (Q7/7)×0.40 + (Q14/14)×0.25 + (Q30/30)×0.20 + (Q60/60)×0.15"
          }
          note="Unità: colli/giorno. Peso maggiore ai dati più recenti." />
        <Step n="2b" label="Indice di rotazione PDV (modalità Venduto)"
          formula="INDICE_ROT = QTA_VENDUTA_MESE / 30"
          note="Unità: pezzi/giorno." />
        <Step n="3" label="Capacità stimata PDV"
          formula="CAPACITA = INDICE_ROT × GIORNI_RESIDUI × COEFF  (0.7 ceduto / 0.8 venduto)"
          note="Quante unità il PDV può assorbire entro la scadenza." />
        <Step n="4" label="Filtro PDV"
          formula="Esclusi: INDICE_ROT < 0.2  oppure  ATTIVO = no"
          note="Soglia minima di rotazione per evitare assegnazioni simboliche." />
        <Step n="5" label="Assegnazione greedy"
          formula="PDV ordinati per CAPACITA desc → QTA_PROPOSTA = min(floor(CAPACITA), stock_residuo)"
          note="Max 10 PDV/referenza in condizioni normali; max 3 se GIORNI_RESIDUI ≤ 2." />
      </div>
    ),
  },

  /* 6 — Fallback articoli senza storico */
  {
    id: 6,
    emoji: '🔄',
    titolo: 'Fallback: articoli senza storico',
    sottotitolo: 'Nessun articolo viene scartato per mancanza di dati',
    corpo: (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
        <p style={p}>
          Se un articolo non ha <b>nessuna riga</b> nei file ceduto/vendite
          (es. nuovo prodotto, mai ceduto nel periodo), il sistema non lo scarta.
          Usa invece la <b>rotazione media</b> degli altri articoli come stima.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {[
            { n: '1', t: 'Calcola media PDV', d: 'Per ogni PDV calcola l\'INDICE_ROT medio su tutti gli articoli con storico.' },
            { n: '2', t: 'Usa come fallback', d: 'L\'articolo senza storico ottiene quella rotazione media, PDV per PDV.' },
            { n: '3', t: 'Segnala l\'avviso', d: 'Nel pannello avvisi compare: "Articolo XXX: nessun ceduto storico — usata media PDV".' },
            { n: '4', t: 'Marca il motivo', d: 'La colonna MOTIVO nel piano riporta il prefisso "(media PDV)" per trasparenza.' },
          ].map(({ n, t, d }) => (
            <div key={n} style={{ display: 'flex', gap: '0.85rem', background: '#f0f7ff', borderRadius: 6, padding: '0.65rem 0.85rem' }}>
              <div style={{ width: 22, height: 22, borderRadius: '50%', background: '#2563ab', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '0.78rem', flexShrink: 0 }}>{n}</div>
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#1a3c6e' }}>{t}</div>
                <div style={{ fontSize: '0.8rem', color: '#495057' }}>{d}</div>
              </div>
            </div>
          ))}
        </div>
        <div style={{ background: '#fff8e1', borderRadius: 6, padding: '0.65rem 0.85rem', fontSize: '0.82rem', color: '#856404' }}>
          <b>Perché è utile:</b> i prodotti nuovi o stagionali hanno storico breve ma possono comunque
          avere una capacità di assorbimento reale. Il fallback garantisce che <b>ogni lotto
          in scadenza riceva una proposta</b>.
        </div>
      </div>
    ),
  },

  /* 7 — Proposte di sconto */
  {
    id: 7,
    emoji: '💰',
    titolo: 'Proposte di sconto',
    sottotitolo: 'Suggerimento automatico quando lo stock non è completamente allocato',
    corpo: (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
        <p style={p}>
          Quando una parte dello stock rimane <b>non allocata</b> (nessun PDV con capacità sufficiente),
          il sistema calcola uno sconto prezzo suggerito in base all'urgenza e alla quota non allocata.
        </p>
        <div style={{ overflowX: 'auto' }}>
          <table style={tbl}>
            <thead>
              <tr>
                {['Condizione', 'Quota non allocata', 'Sconto proposto'].map(h => (
                  <th key={h} style={th}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                ['Giorni residui ≤ 2', 'qualsiasi', '40%'],
                ['Giorni residui ≤ 5', 'qualsiasi', '25%'],
                ['Giorni residui ≤ 10', '> 50%', '20%'],
                ['Giorni residui ≤ 7', '> 25%', '15%'],
                ['Tutto allocato', '—', 'nessuno'],
                ['Bassa urgenza', 'bassa', 'nessuno'],
              ].map((row, i) => (
                <tr key={i}>
                  <td style={td(i)}>{row[0]}</td>
                  <td style={td(i)}>{row[1]}</td>
                  <td style={{ ...td(i), fontWeight: 700, color: row[2] === 'nessuno' ? '#6c757d' : '#dc3545' }}>{row[2]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div style={{ background: '#f0fff4', borderRadius: 6, padding: '0.65rem 0.85rem', fontSize: '0.82rem', color: '#155724' }}>
          <b>Nota operativa:</b> lo sconto è una <b>raccomandazione</b>. È l'operatore a decidere
          se e come applicarlo sul sistema di vendita. La colonna <code style={{ background: 'rgba(0,0,0,0.07)', padding: '0.1rem 0.3rem', borderRadius: 3 }}>SCONTO_PROPOSTO</code> nel
          file Excel riporta il valore (es. 0.25 = 25%) oppure è vuota.
        </div>
      </div>
    ),
  },

  /* 8 — Output operativo */
  {
    id: 8,
    emoji: '📋',
    titolo: 'Output operativo',
    sottotitolo: 'piano_operativo.xlsx — una riga per ogni assegnazione LOTTO → PDV',
    corpo: (
      <>
        <div style={{ overflowX: 'auto', marginBottom: '0.75rem' }}>
          <table style={tbl}>
            <thead>
              <tr>
                {['Colonna', 'Descrizione'].map(h => <th key={h} style={th}>{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {[
                ['LOTTO', 'Identificativo lotto'],
                ['COD_ARTICOLO', 'Codice prodotto'],
                ['DESCRIZIONE_ARTICOLO', 'Nome prodotto'],
                ['COD_PDV / NOME_PDV', 'Punto vendita assegnatario'],
                ['GIORNI_RESIDUI', 'Giorni alla scadenza al momento dell\'elaborazione'],
                ['INDICE_ROT', 'Indice di rotazione calcolato per quel PDV'],
                ['CAPACITA_STIMATA', 'Stima unità assorbibili entro scadenza'],
                ['QTA_PROPOSTA', 'Quantità da inviare (colli o pezzi)'],
                ['UM', '"colli" in modalità Ceduto — "pezzi" in modalità Venduto'],
                ['PRIORITA', 'Alta (≤5gg) / Media (≤15gg) / Bassa'],
                ['MOTIVO', 'Motivazione assegnazione; "(media PDV)" se fallback'],
                ['SCONTO_PROPOSTO', '0.15–0.40 se suggerito, vuoto altrimenti'],
              ].map(([col, desc], i) => (
                <tr key={col}>
                  <td style={{ ...td(i), fontFamily: 'monospace', fontSize: '0.75rem', whiteSpace: 'nowrap', color: '#1a3c6e', fontWeight: 600 }}>{col}</td>
                  <td style={td(i)}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p style={{ fontSize: '0.78rem', color: '#6c757d' }}>
          Il piano è ordinato per priorità decrescente: Alta → Media → Bassa.
        </p>
      </>
    ),
  },

  /* 9 — Priorità e limiti */
  {
    id: 9,
    emoji: '⚡',
    titolo: 'Priorità e regole operative',
    sottotitolo: 'Parametri che guidano l\'assegnazione',
    corpo: (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={tbl}>
            <thead>
              <tr>{['Parametro', 'Valore', 'Motivo'].map(h => <th key={h} style={th}>{h}</th>)}</tr>
            </thead>
            <tbody>
              {[
                ['Priorità Alta', 'giorni residui ≤ 5', 'Urgenza massima, distribuire subito'],
                ['Priorità Media', 'giorni residui ≤ 15', 'Monitoraggio attivo'],
                ['Priorità Bassa', 'giorni residui > 15', 'Pianificazione normale'],
                ['Giorni critici', '≤ 2', 'Riduce max PDV a 3 per concentrare le consegne'],
                ['Max PDV (normale)', '10', 'Limite operativo per referenza'],
                ['Max PDV (critico)', '3', 'Con ≤2gg c\'è tempo solo per una consegna urgente'],
                ['Soglia indice min', '0.2', 'Esclude PDV che vendono troppo poco per assorbire stock'],
              ].map((row, i) => (
                <tr key={row[0]}>
                  {row.map((cell, j) => (
                    <td key={j} style={{ ...td(i), fontWeight: j === 0 ? 600 : 400, color: j === 1 ? '#1a3c6e' : undefined }}>{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div style={{ background: '#f8fafc', borderRadius: 6, padding: '0.75rem 1rem', fontSize: '0.82rem', color: '#374151' }}>
          <b>Rielaborazione:</b> puoi rielaborare più volte nella stessa sessione cambiando modalità
          senza ricaricare i file. I dati rimangono in memoria fino al riavvio del servizio.
        </div>
      </div>
    ),
  },

  /* 10 — FAQ */
  {
    id: 10,
    emoji: '❓',
    titolo: 'Domande frequenti',
    sottotitolo: 'FAQ operative',
    corpo: (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
        {[
          {
            q: 'Posso caricare solo CEDUTO_7GG senza gli altri?',
            a: 'Sì. Il 7gg è l\'unico obbligatorio in modalità Ceduto. Gli altri affinano la stima ma non sono richiesti.',
          },
          {
            q: 'Cosa cambia se carico anche il CEDUTO_60GG?',
            a: 'Attiva la formula a 4 finestre (40/25/20/15%) invece di quella a 3 (50/30/20%). Più stabile per articoli con bassa frequenza o stagionalità.',
          },
          {
            q: 'Un PDV non ha mai ricevuto quell\'articolo. Viene escluso?',
            a: 'Solo se il suo indice di rotazione medio è sotto 0.2. Altrimenti il meccanismo fallback lo può proporre con rotazione media.',
          },
          {
            q: 'Cosa significa SCONTO_PROPOSTO = 0.25?',
            a: 'Il sistema suggerisce uno sconto del 25%. Applicarlo è una decisione commerciale dell\'operatore — il tool non modifica prezzi.',
          },
          {
            q: 'Cosa significa "(media PDV)" nel campo MOTIVO?',
            a: 'L\'articolo non aveva storico nel periodo analizzato. La capacità del PDV è stimata con la rotazione media degli altri articoli.',
          },
          {
            q: 'I file Excel devono avere un formato specifico?',
            a: 'Bastano le colonne indicate (nomi esatti). L\'ordine delle colonne è irrilevante. I codici numerici (lotto, articolo, PDV) vengono gestiti automaticamente come testo.',
          },
        ].map(({ q, a }, i) => (
          <div key={i} style={{ background: i % 2 === 0 ? '#f8fafc' : '#fff', borderRadius: 6, padding: '0.65rem 0.85rem', border: '1px solid #e2e8f0' }}>
            <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#1a3c6e', marginBottom: '0.2rem' }}>Q: {q}</div>
            <div style={{ fontSize: '0.82rem', color: '#495057' }}>A: {a}</div>
          </div>
        ))}
      </div>
    ),
  },
]

export default function Presentazione() {
  const [slide, setSlide] = useState(0)
  const current = SLIDES[slide]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: 780, margin: '0 auto' }}>

      {/* ── SLIDE CARD ── */}
      <div style={{ background: '#fff', borderRadius: 12, boxShadow: '0 2px 12px rgba(0,0,0,0.09)', overflow: 'hidden' }}>
        {/* Header */}
        <div style={{ background: 'linear-gradient(135deg, #1a3c6e 0%, #2563ab 100%)', padding: '1.5rem 1.75rem', color: '#fff' }}>
          <div style={{ fontSize: '2.2rem', marginBottom: '0.4rem' }}>{current.emoji}</div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 800, margin: 0 }}>{current.titolo}</h1>
          <p style={{ margin: '0.3rem 0 0', opacity: 0.85, fontSize: '0.9rem' }}>{current.sottotitolo}</p>
          {/* Progress bar */}
          <div style={{ display: 'flex', gap: '0.3rem', marginTop: '1rem' }}>
            {SLIDES.map((_, i) => (
              <button key={i} onClick={() => setSlide(i)} style={{
                height: 4, flex: 1, border: 'none', borderRadius: 2,
                background: i === slide ? '#fff' : 'rgba(255,255,255,0.35)',
                cursor: 'pointer', padding: 0, transition: 'background 0.2s',
              }} />
            ))}
          </div>
        </div>

        {/* Corpo */}
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
            border: '1.5px solid #dee2e6', fontWeight: 600,
            cursor: slide === 0 ? 'not-allowed' : 'pointer', fontSize: '0.88rem',
          }}
        >
          ← Precedente
        </button>
        <span style={{ fontSize: '0.82rem', color: '#6c757d' }}>{slide + 1} / {SLIDES.length}</span>
        <button
          onClick={() => setSlide(s => Math.min(SLIDES.length - 1, s + 1))}
          disabled={slide === SLIDES.length - 1}
          style={{
            padding: '0.45rem 1.2rem', borderRadius: 6,
            background: slide === SLIDES.length - 1 ? '#e2e8f0' : 'linear-gradient(135deg,#1a3c6e,#2563ab)',
            color: slide === SLIDES.length - 1 ? '#adb5bd' : '#fff',
            border: 'none', fontWeight: 600,
            cursor: slide === SLIDES.length - 1 ? 'not-allowed' : 'pointer', fontSize: '0.88rem',
            boxShadow: slide === SLIDES.length - 1 ? 'none' : '0 2px 6px rgba(26,60,110,0.25)',
          }}
        >
          Successivo →
        </button>
      </div>

      {/* ── INDICE ── */}
      <div style={{ background: '#fff', borderRadius: 10, padding: '1rem 1.5rem', boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}>
        <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#6c757d', marginBottom: '0.6rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Indice
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
          {SLIDES.map((s, i) => (
            <button key={i} onClick={() => setSlide(i)} style={{
              padding: '0.25rem 0.7rem', borderRadius: 20,
              background: i === slide ? '#1a3c6e' : '#f0f4f8',
              color: i === slide ? '#fff' : '#495057',
              border: 'none', cursor: 'pointer',
              fontSize: '0.78rem', fontWeight: i === slide ? 700 : 400,
              transition: 'all 0.15s',
            }}>
              {s.emoji} {s.titolo}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

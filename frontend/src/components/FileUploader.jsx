/**
 * Componente upload file Excel.
 *
 * Per i file ceduto (tipo ceduto_*):
 *   - legge il file nel browser con SheetJS
 *   - applica la trasformazione (colonne posizionali → colonne nominate)
 *   - invia solo i dati estratti come JSON → bypassa il limite 4.5 MB di Vercel
 *
 * Per tutti gli altri tipi:
 *   - upload multipart standard
 */

import React, { useRef, useState } from 'react'
import useStore from '../store.js'
import InfoTooltip from './InfoTooltip.jsx'

// Tipi ceduto con il periodo corrispondente
const CEDUTO_PERIODI = {
  ceduto_7gg:  '7GG',
  ceduto_14gg: '14GG',
  ceduto_30gg: '30GG',
  ceduto_60gg: '60GG',
}

/**
 * Legge un file ceduto grezzo con SheetJS (client-side) e restituisce
 * un array di righe con le colonne standard.
 * Replica la logica di trasforma_ceduto_raw nel backend.
 */
async function elaboraCedutoClientSide(file, periodo) {
  const XLSX = await import('xlsx')

  const arrayBuffer = await file.arrayBuffer()
  const workbook = XLSX.read(arrayBuffer, {
    type: 'array',
    raw: true,        // non interpretare date/formati
    cellNF: false,
    cellText: false,
  })

  const righe = []

  for (const sheetName of workbook.SheetNames) {
    const sheet = workbook.Sheets[sheetName]
    // Ottieni come array di array, raw=true per evitare conversioni automatiche
    const data = XLSX.utils.sheet_to_json(sheet, {
      header: 1,
      raw: true,
      defval: '',
      blankrows: false,
    })

    // Salta la riga 0 (header), processa dal secondo in poi
    for (let i = 1; i < data.length; i++) {
      const row = data[i]
      if (!row || row.length <= 18) continue

        // Indici 0-based (colonne 1-based del documento → -1):
      // col9(1b)→idx8=Radice, col10(1b)→idx9=Variante, col12(1b)→idx11=TipoMov
      // col14(1b)→idx13=Pezzi, col15(1b)→idx14=Imballo
      // col17(1b)→idx16=CodPDV, col18(1b)→idx17=NomePDV

      // Col 9 (1-based) = idx 8 = Radice — deve essere numerica
      const radiceRaw = row[8]
      if (radiceRaw === '' || radiceRaw === null || radiceRaw === undefined) continue
      if (isNaN(Number(radiceRaw))) continue

      // Col 12 (1-based) = idx 11 = TipoMov — deve essere "L"
      const tipoMov = String(row[11] ?? '').trim().toUpperCase()
      if (tipoMov !== 'L') continue

      // Col 14 (1-based) = idx 13 = Pezzi
      // Col 15 (1-based) = idx 14 = Imballo
      const pezzi   = Math.round(Number(row[13]) || 0)
      const imballo = Number(row[14]) || 0
      const imballoEff = imballo <= 0 ? 1 : imballo
      const colli   = Math.round(pezzi / imballoEff)

      // Scarta valori negativi
      if (pezzi < 0 || colli < 0) continue

      // COD_ARTICOLO: idx 8 (Radice) + idx 9 (Variante) zero-padded a 2 cifre
      const radiceStr   = String(Math.round(Number(radiceRaw)))
      const variante    = Number(row[9]) || 0
      const varianteStr = String(Math.round(variante)).padStart(2, '0')
      const codArticolo = radiceStr + varianteStr

      // COD_PDV: idx 16 — 6 cifre con "0" finale → rimuovi l'ultimo zero
      let codPdv = String(Math.round(Number(row[16]) || 0))
      if (codPdv.length === 6 && codPdv.endsWith('0')) {
        codPdv = codPdv.slice(0, -1)
      }

      // NomePDV: idx 17
      const nomePdv = String(row[17] ?? '').trim()

      righe.push({
        COD_PDV:      codPdv,
        NOME_PDV:     nomePdv,
        COD_ARTICOLO: codArticolo,
        [`QTA_CEDUTA_${periodo}_COLLI`]: colli,
        [`QTA_CEDUTA_${periodo}_PEZZI`]: pezzi,
      })
    }
  }

  if (righe.length === 0) {
    throw new Error(
      'Nessuna riga valida trovata. ' +
      'Verifica che il file contenga righe con tipo movimento "L" e colonna 9 numerica.'
    )
  }

  return righe
}

export default function FileUploader({ tipo, label, obbligatorio = false, infoTitle, infoContent }) {
  const { apiHeaders, markFileCaricato, filesCaricati } = useStore()
  const [stato, setStato] = useState(null)   // null | "ok" | "errore" | "loading"
  const [msg, setMsg]     = useState('')
  const inputRef = useRef()

  const caricato = filesCaricati[tipo]
  const isCeduto = tipo in CEDUTO_PERIODI

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setStato('loading')
    setMsg(isCeduto ? 'Lettura file…' : 'Caricamento…')

    try {
      if (isCeduto) {
        // ── Elaborazione client-side (bypass limite 4.5 MB Vercel) ──────────
        const periodo = CEDUTO_PERIODI[tipo]
        setMsg('Elaborazione righe…')
        const righe = await elaboraCedutoClientSide(file, periodo)

        // Invia a chunk da 2000 righe per rispettare il limite 4.5 MB Vercel
        const CHUNK_SIZE = 2000
        const chunks = []
        for (let i = 0; i < righe.length; i += CHUNK_SIZE) {
          chunks.push(righe.slice(i, i + CHUNK_SIZE))
        }

        let lastData = null
        for (let i = 0; i < chunks.length; i++) {
          const isLast = i === chunks.length - 1
          setMsg(`Invio dati… (${i + 1}/${chunks.length})`)
          const res = await fetch(`/api/upload/json/${tipo}`, {
            method: 'POST',
            headers: { ...apiHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify({ righe: chunks[i], is_last_chunk: isLast }),
          })
          const text = await res.text()
          let data
          try { data = JSON.parse(text) } catch (_) { data = { detail: text } }
          if (!res.ok) {
            setStato('errore')
            setMsg(data.detail || 'Errore sconosciuto')
            return
          }
          if (isLast) lastData = data
        }

        setStato('ok')
        setMsg(`${lastData?.righe ?? righe.length} righe elaborate`)
        markFileCaricato(tipo)
      } else {
        // ── Upload multipart standard (file piccoli) ──────────────────────────
        const formData = new FormData()
        formData.append('file', file)

        const res = await fetch(`/api/upload/${tipo}`, {
          method: 'POST',
          headers: apiHeaders(),
          body: formData,
        })
        const text = await res.text()
        let data
        try { data = JSON.parse(text) } catch (_) { data = { detail: text } }

        if (!res.ok) {
          setStato('errore')
          setMsg(data.detail || 'Errore sconosciuto')
        } else {
          setStato('ok')
          setMsg(`${data.righe} righe caricate`)
          markFileCaricato(tipo)
        }
      }
    } catch (err) {
      setStato('errore')
      setMsg(err.message || 'Errore imprevisto')
    }

    inputRef.current.value = ''
  }

  const isOk = caricato || stato === 'ok'

  return (
    <div style={{ marginBottom: '0.9rem' }}>
      {/* Label row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.35rem' }}>
        <span style={{ fontWeight: 700, fontSize: '0.83rem', color: '#1a202c' }}>
          {label}
          {obbligatorio && <span style={{ color: '#dc3545', marginLeft: 2 }}>*</span>}
        </span>
        {infoContent && (
          <InfoTooltip title={infoTitle || label}>
            {infoContent}
          </InfoTooltip>
        )}
      </div>

      {/* Upload row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
        <button
          onClick={() => inputRef.current.click()}
          disabled={stato === 'loading'}
          style={{
            padding: '0.3rem 0.85rem',
            background: isOk ? '#e8f5e9' : stato === 'loading' ? '#9eb3cc' : '#1a3c6e',
            color: isOk ? '#155724' : '#fff',
            border: isOk ? '1.5px solid #a5d6a7' : 'none',
            borderRadius: 5,
            cursor: stato === 'loading' ? 'not-allowed' : 'pointer',
            fontSize: '0.82rem', fontWeight: 600,
            transition: 'all 0.15s', whiteSpace: 'nowrap',
          }}
        >
          {stato === 'loading' ? '⏳ ' + msg : isOk ? '✓ Cambia file' : '📂 Scegli file'}
        </button>

        {isOk && stato !== 'loading' && (
          <span style={{
            fontSize: '0.78rem', background: '#d4edda', color: '#155724',
            padding: '0.15rem 0.55rem', borderRadius: 10,
          }}>
            {msg || 'Caricato'}
          </span>
        )}
        {stato === 'errore' && (
          <span style={{
            fontSize: '0.78rem', background: '#f8d7da', color: '#721c24',
            padding: '0.15rem 0.55rem', borderRadius: 10,
            maxWidth: 280, wordBreak: 'break-word',
          }}>
            ✗ {msg}
          </span>
        )}

        <input
          ref={inputRef}
          type="file"
          accept=".xlsx,.xls"
          style={{ display: 'none' }}
          onChange={handleUpload}
        />
      </div>
    </div>
  )
}

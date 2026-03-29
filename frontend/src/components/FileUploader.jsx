/**
 * Componente upload file Excel con bottone info (?).
 */

import React, { useRef, useState } from 'react'
import useStore from '../store.js'
import InfoTooltip from './InfoTooltip.jsx'

export default function FileUploader({ tipo, label, obbligatorio = false, infoTitle, infoContent }) {
  const { apiHeaders, markFileCaricato, filesCaricati } = useStore()
  const [stato, setStato] = useState(null)   // null | "ok" | "errore" | "loading"
  const [msg, setMsg] = useState('')
  const inputRef = useRef()

  const caricato = filesCaricati[tipo]

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    setStato('loading')
    setMsg('')

    try {
      const res = await fetch(`/api/upload/${tipo}`, {
        method: 'POST',
        headers: apiHeaders(),
        body: formData,
      })
      const data = await res.json()
      if (!res.ok) {
        setStato('errore')
        setMsg(data.detail || 'Errore sconosciuto')
      } else {
        setStato('ok')
        setMsg(`${data.righe} righe caricate`)
        markFileCaricato(tipo)
      }
    } catch (err) {
      setStato('errore')
      setMsg('Errore di rete: ' + err.message)
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
          style={{
            padding: '0.3rem 0.85rem',
            background: isOk ? '#e8f5e9' : '#1a3c6e',
            color: isOk ? '#155724' : '#fff',
            border: isOk ? '1.5px solid #a5d6a7' : 'none',
            borderRadius: 5, cursor: 'pointer', fontSize: '0.82rem',
            fontWeight: 600, transition: 'all 0.15s', whiteSpace: 'nowrap',
          }}
        >
          {isOk ? '✓ Cambia file' : '📂 Scegli file'}
        </button>

        {stato === 'loading' && (
          <span style={{ fontSize: '0.78rem', color: '#6c757d' }}>Caricamento…</span>
        )}
        {isOk && (
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

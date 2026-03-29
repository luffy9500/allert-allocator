/**
 * Componente generico per l'upload di un file Excel.
 * Mostra lo stato (non caricato / caricato / errore).
 */

import React, { useRef, useState } from 'react'
import useStore from '../store.js'

const styles = {
  wrap: { marginBottom: '0.75rem' },
  label: { display: 'block', fontWeight: 600, marginBottom: '0.3rem', fontSize: '0.88rem' },
  row: { display: 'flex', alignItems: 'center', gap: '0.75rem' },
  btn: {
    padding: '0.35rem 0.9rem', background: '#1a3c6e', color: '#fff',
    border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: '0.85rem',
  },
  badge: (ok) => ({
    fontSize: '0.8rem', padding: '0.2rem 0.6rem', borderRadius: 10,
    background: ok ? '#d4edda' : '#f8d7da',
    color: ok ? '#155724' : '#721c24',
  }),
  hint: { fontSize: '0.78rem', color: '#6c757d', marginTop: '0.2rem' },
}

/**
 * @param {object} props
 * @param {string} props.tipo     - es. "cedi_scadenze"
 * @param {string} props.label    - es. "CEDI_SCADENZE"
 * @param {string} props.hint     - descrizione colonne attese
 */
export default function FileUploader({ tipo, label, hint }) {
  const { sessionId, apiHeaders, markFileCaricato, filesCaricati } = useStore()
  const [stato, setStato] = useState(null)   // null | "ok" | "errore"
  const [msg, setMsg] = useState('')
  const inputRef = useRef()

  const caricato = filesCaricati[tipo]

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    setStato(null)
    setMsg('Caricamento...')

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
        setMsg(data.messaggio)
        markFileCaricato(tipo)
      }
    } catch (err) {
      setStato('errore')
      setMsg('Errore di rete: ' + err.message)
    }

    // Reset input per permettere ri-upload dello stesso file
    inputRef.current.value = ''
  }

  return (
    <div style={styles.wrap}>
      <label style={styles.label}>{label}</label>
      <div style={styles.row}>
        <button style={styles.btn} onClick={() => inputRef.current.click()}>
          Scegli file
        </button>
        {(caricato || stato) && (
          <span style={styles.badge(caricato || stato === 'ok')}>
            {caricato && stato !== 'errore' ? 'Caricato' : stato === 'errore' ? 'Errore' : msg}
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
      {stato === 'errore' && <p style={{ ...styles.hint, color: '#dc3545' }}>{msg}</p>}
      {stato === 'ok' && <p style={styles.hint}>{msg}</p>}
      {hint && !stato && <p style={styles.hint}>{hint}</p>}
    </div>
  )
}

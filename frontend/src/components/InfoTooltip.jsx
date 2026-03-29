/**
 * Bottone "?" con popup informativo al click.
 * Si chiude cliccando fuori o premendo Esc.
 */

import React, { useState, useEffect, useRef } from 'react'

export default function InfoTooltip({ title, children }) {
  const [open, setOpen] = useState(false)
  const ref = useRef()

  useEffect(() => {
    if (!open) return
    const onKey = (e) => e.key === 'Escape' && setOpen(false)
    const onOutside = (e) => ref.current && !ref.current.contains(e.target) && setOpen(false)
    document.addEventListener('keydown', onKey)
    document.addEventListener('mousedown', onOutside)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.removeEventListener('mousedown', onOutside)
    }
  }, [open])

  return (
    <span style={{ position: 'relative', display: 'inline-block' }} ref={ref}>
      <button
        onClick={() => setOpen(v => !v)}
        title="Info"
        style={{
          width: 18, height: 18, borderRadius: '50%',
          background: open ? '#1a3c6e' : '#dbe8f8',
          color: open ? '#fff' : '#1a3c6e',
          border: '1.5px solid #1a3c6e',
          fontSize: '0.7rem', fontWeight: 800,
          cursor: 'pointer', lineHeight: 1,
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0, padding: 0,
          transition: 'all 0.15s',
        }}
      >
        ?
      </button>

      {open && (
        <div style={{
          position: 'absolute', top: '24px', left: '50%',
          transform: 'translateX(-50%)',
          background: '#1a3c6e', color: '#fff',
          borderRadius: 8, padding: '0.9rem 1.1rem',
          width: 300, zIndex: 1000,
          boxShadow: '0 4px 20px rgba(0,0,0,0.25)',
          fontSize: '0.82rem', lineHeight: 1.5,
        }}>
          {/* Freccia */}
          <div style={{
            position: 'absolute', top: -7, left: '50%',
            transform: 'translateX(-50%)',
            width: 0, height: 0,
            borderLeft: '7px solid transparent',
            borderRight: '7px solid transparent',
            borderBottom: '7px solid #1a3c6e',
          }} />
          {title && (
            <div style={{ fontWeight: 700, marginBottom: '0.5rem', fontSize: '0.88rem' }}>
              {title}
            </div>
          )}
          {children}
        </div>
      )}
    </span>
  )
}

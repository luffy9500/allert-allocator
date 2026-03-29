/**
 * Toggle visibile in header: permette di scegliere tra
 * modalità "CEDUTO CEDI" e "VENDUTO PDV".
 */

import React from 'react'
import useStore from '../store.js'

const styles = {
  wrap: { display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.82rem' },
  label: { color: '#c8d8f0' },
  toggle: {
    display: 'flex', borderRadius: 20, overflow: 'hidden',
    border: '1px solid rgba(255,255,255,0.3)',
  },
  btn: (active) => ({
    padding: '0.3rem 0.8rem',
    background: active ? '#fff' : 'transparent',
    color: active ? '#1a3c6e' : '#c8d8f0',
    border: 'none', cursor: 'pointer',
    fontWeight: active ? 700 : 400,
    fontSize: '0.82rem',
    transition: 'all 0.15s',
  }),
}

export default function ModalityToggle() {
  const { modalita, setModalita, resetRisultato } = useStore()

  const handleSwitch = (m) => {
    if (m !== modalita) {
      setModalita(m)
      resetRisultato()
    }
  }

  return (
    <div style={styles.wrap}>
      <span style={styles.label}>Fonte:</span>
      <div style={styles.toggle}>
        <button style={styles.btn(modalita === 'ceduto')} onClick={() => handleSwitch('ceduto')}>
          Ceduto CEDI
        </button>
        <button style={styles.btn(modalita === 'venduto')} onClick={() => handleSwitch('venduto')}>
          Venduto PDV
        </button>
      </div>
    </div>
  )
}

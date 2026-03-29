/**
 * Card numerica per la Dashboard.
 */

import React from 'react'

const styles = {
  card: {
    background: '#fff', borderRadius: 8, padding: '1.25rem 1.5rem',
    boxShadow: '0 1px 4px rgba(0,0,0,0.08)', minWidth: 160,
  },
  label: { fontSize: '0.82rem', color: '#6c757d', marginBottom: '0.4rem' },
  value: (color) => ({
    fontSize: '2rem', fontWeight: 700,
    color: color || '#1a3c6e',
    lineHeight: 1.1,
  }),
  sub: { fontSize: '0.78rem', color: '#adb5bd', marginTop: '0.3rem' },
}

export default function StatsCard({ label, value, color, sub }) {
  return (
    <div style={styles.card}>
      <div style={styles.label}>{label}</div>
      <div style={styles.value(color)}>{value ?? '—'}</div>
      {sub && <div style={styles.sub}>{sub}</div>}
    </div>
  )
}

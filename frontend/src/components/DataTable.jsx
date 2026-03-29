/**
 * Tabella dati generica con ordinamento per colonna.
 *
 * Props:
 *  columns: [{ key, label, render? }]
 *  rows:    array di oggetti
 *  onRowClick?: (row) => void
 */

import React, { useState } from 'react'

const PRIORITA_COLOR = { Alta: '#dc3545', Media: '#fd7e14', Bassa: '#198754' }

const styles = {
  wrap: { overflowX: 'auto' },
  table: {
    width: '100%', borderCollapse: 'collapse',
    fontSize: '0.85rem', background: '#fff',
    boxShadow: '0 1px 4px rgba(0,0,0,0.08)', borderRadius: 8,
  },
  th: (sorted) => ({
    padding: '0.65rem 0.9rem', textAlign: 'left',
    background: '#f0f4fa', fontWeight: 600,
    fontSize: '0.8rem', cursor: 'pointer', userSelect: 'none',
    borderBottom: '2px solid #dee2e6',
    color: sorted ? '#1a3c6e' : '#495057',
    whiteSpace: 'nowrap',
  }),
  td: { padding: '0.55rem 0.9rem', borderBottom: '1px solid #f0f0f0' },
  tr: (clickable) => ({
    cursor: clickable ? 'pointer' : 'default',
    transition: 'background 0.1s',
  }),
  badge: (p) => ({
    display: 'inline-block', padding: '0.15rem 0.55rem',
    borderRadius: 10, fontSize: '0.75rem', fontWeight: 600,
    background: PRIORITA_COLOR[p] + '20',
    color: PRIORITA_COLOR[p] || '#495057',
  }),
  empty: { padding: '2rem', textAlign: 'center', color: '#adb5bd' },
}

function sortRows(rows, key, dir) {
  if (!key) return rows
  return [...rows].sort((a, b) => {
    const va = a[key], vb = b[key]
    if (va === vb) return 0
    const cmp = va < vb ? -1 : 1
    return dir === 'asc' ? cmp : -cmp
  })
}

export default function DataTable({ columns, rows, onRowClick }) {
  const [sortKey, setSortKey] = useState(null)
  const [sortDir, setSortDir] = useState('asc')

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  const sorted = sortRows(rows, sortKey, sortDir)

  return (
    <div style={styles.wrap}>
      <table style={styles.table}>
        <thead>
          <tr>
            {columns.map(col => (
              <th
                key={col.key}
                style={styles.th(sortKey === col.key)}
                onClick={() => handleSort(col.key)}
              >
                {col.label}
                {sortKey === col.key ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ''}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.length === 0 ? (
            <tr>
              <td colSpan={columns.length} style={styles.empty}>
                Nessun dato disponibile.
              </td>
            </tr>
          ) : sorted.map((row, i) => (
            <tr
              key={i}
              style={styles.tr(!!onRowClick)}
              onClick={() => onRowClick?.(row)}
              onMouseEnter={e => onRowClick && (e.currentTarget.style.background = '#f8f9fa')}
              onMouseLeave={e => (e.currentTarget.style.background = '')}
            >
              {columns.map(col => (
                <td key={col.key} style={styles.td}>
                  {col.key === 'priorita' || col.key === 'PRIORITA' ? (
                    <span style={styles.badge(row[col.key])}>{row[col.key]}</span>
                  ) : col.render ? (
                    col.render(row[col.key], row)
                  ) : (
                    row[col.key] ?? '—'
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

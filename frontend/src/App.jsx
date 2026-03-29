import React from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import ModalityToggle from './components/ModalityToggle.jsx'
import Dashboard from './pages/Dashboard.jsx'
import ElencoReferenze from './pages/ElencoReferenze.jsx'
import DettaglioReferenza from './pages/DettaglioReferenza.jsx'
import PianoOperativo from './pages/PianoOperativo.jsx'

const NAV_LINKS = [
  { to: '/',         label: 'Dashboard'   },
  { to: '/referenze', label: 'Referenze'  },
  { to: '/piano',    label: 'Piano Op.'   },
]

const styles = {
  shell: { display: 'flex', flexDirection: 'column', minHeight: '100vh' },
  header: {
    background: '#1a3c6e', color: '#fff', padding: '0 1.5rem',
    display: 'flex', alignItems: 'center', gap: '2rem', height: 56,
  },
  brand: { fontWeight: 700, fontSize: '1.1rem', letterSpacing: '0.02em', whiteSpace: 'nowrap' },
  nav: { display: 'flex', gap: '0.25rem', flex: 1 },
  navLink: {
    color: '#c8d8f0', textDecoration: 'none', padding: '0.4rem 0.9rem',
    borderRadius: 4, fontSize: '0.9rem',
  },
  navLinkActive: { background: 'rgba(255,255,255,0.15)', color: '#fff' },
  main: { flex: 1, padding: '1.5rem', maxWidth: 1200, width: '100%', margin: '0 auto' },
}

export default function App() {
  return (
    <BrowserRouter>
      <div style={styles.shell}>
        <header style={styles.header}>
          <span style={styles.brand}>Allert Allocator</span>
          <nav style={styles.nav}>
            {NAV_LINKS.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                style={({ isActive }) => ({
                  ...styles.navLink,
                  ...(isActive ? styles.navLinkActive : {}),
                })}
              >
                {label}
              </NavLink>
            ))}
          </nav>
          <ModalityToggle />
        </header>

        <main style={styles.main}>
          <Routes>
            <Route path="/"                          element={<Dashboard />} />
            <Route path="/referenze"                 element={<ElencoReferenze />} />
            <Route path="/referenze/:codArticolo"    element={<DettaglioReferenza />} />
            <Route path="/piano"                     element={<PianoOperativo />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

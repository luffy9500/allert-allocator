import React from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import ModalityToggle from './components/ModalityToggle.jsx'
import Dashboard from './pages/Dashboard.jsx'
import ElencoReferenze from './pages/ElencoReferenze.jsx'
import DettaglioReferenza from './pages/DettaglioReferenza.jsx'
import PianoOperativo from './pages/PianoOperativo.jsx'
import Presentazione from './pages/Presentazione.jsx'

const NAV_LINKS = [
  { to: '/',           label: 'Dashboard'    },
  { to: '/referenze',  label: 'Referenze'    },
  { to: '/piano',      label: 'Piano Op.'    },
  { to: '/info',       label: '📋 Info Tool' },
]

export default function App() {
  return (
    <BrowserRouter>
      <div style={{
        display: 'flex', flexDirection: 'column',
        height: '100vh', overflow: 'hidden',
        background: '#f0f4f8',
      }}>
        {/* ── HEADER ── */}
        <header style={{
          background: 'linear-gradient(135deg, #1a3c6e 0%, #2563ab 100%)',
          color: '#fff', padding: '0 1.5rem',
          display: 'flex', alignItems: 'center', gap: '1.5rem',
          height: 54, flexShrink: 0,
          boxShadow: '0 2px 8px rgba(0,0,0,0.25)',
          zIndex: 100,
        }}>
          {/* Brand */}
          <NavLink to="/info" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '1.3rem' }}>🔔</span>
            <span style={{ fontWeight: 800, fontSize: '1.05rem', letterSpacing: '0.03em', color: '#fff', whiteSpace: 'nowrap' }}>
              Allert Allocator
            </span>
          </NavLink>

          {/* Nav */}
          <nav style={{ display: 'flex', gap: '0.15rem', flex: 1 }}>
            {NAV_LINKS.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                style={({ isActive }) => ({
                  color: isActive ? '#fff' : '#b8d0f0',
                  textDecoration: 'none',
                  padding: '0.35rem 0.85rem',
                  borderRadius: 5,
                  fontSize: '0.88rem',
                  fontWeight: isActive ? 700 : 400,
                  background: isActive ? 'rgba(255,255,255,0.18)' : 'transparent',
                  transition: 'all 0.15s',
                })}
              >
                {label}
              </NavLink>
            ))}
          </nav>

          <ModalityToggle />
        </header>

        {/* ── MAIN (scrollabile) ── */}
        <main style={{
          flex: 1, overflowY: 'auto',
          padding: '1.5rem',
        }}>
          <div style={{ maxWidth: 1280, margin: '0 auto' }}>
            <Routes>
              <Route path="/"                        element={<Dashboard />} />
              <Route path="/referenze"               element={<ElencoReferenze />} />
              <Route path="/referenze/:codArticolo"  element={<DettaglioReferenza />} />
              <Route path="/piano"                   element={<PianoOperativo />} />
              <Route path="/info"                    element={<Presentazione />} />
            </Routes>
          </div>
        </main>
      </div>
    </BrowserRouter>
  )
}

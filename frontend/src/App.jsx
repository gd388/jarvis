import { useState, useEffect, useRef, useCallback } from 'react'
import './App.css'

const STATUS = {
  standby:   'IDLE',
  wake:      'ONLINE',
  listening: 'LISTENING',
  thinking:  'THINKING',
  speaking:  'SPEAKING',
}

/* ── Mini arc-reactor orb (SVG) ───────────────────────────── */
function MiniOrb({ state }) {
  return (
    <svg className={`mini-orb orb-${state}`} viewBox="0 0 100 100" aria-hidden="true">
      <defs>
        <radialGradient id="gc">
          <stop offset="0%"  stopColor="#fff"    stopOpacity="0.95" />
          <stop offset="40%" stopColor="#00d4ff" stopOpacity="0.7" />
          <stop offset="100%" stopColor="#003050" stopOpacity="0" />
        </radialGradient>
        <filter id="gl"><feGaussianBlur stdDeviation="2" /></filter>
      </defs>
      {/* outer ring */}
      <g className="ring-a"><circle cx="50" cy="50" r="42" fill="none"
        stroke="#00d4ff" strokeWidth="1.2" strokeDasharray="30 10 50 10"
        strokeLinecap="round" /></g>
      {/* mid ring */}
      <g className="ring-b"><circle cx="50" cy="50" r="33" fill="none"
        stroke="#00d4ff" strokeWidth="1" strokeDasharray="45 15"
        strokeLinecap="round" opacity="0.7" /></g>
      {/* core */}
      <circle cx="50" cy="50" r="18" fill="none" stroke="#00d4ff"
        strokeWidth="1.5" filter="url(#gl)" className="core-ring" />
      {/* spokes */}
      {[0, 60, 120, 180, 240, 300].map(d => {
        const r = (d * Math.PI) / 180
        return <line key={d}
          x1={50 + Math.cos(r) * 8}  y1={50 + Math.sin(r) * 8}
          x2={50 + Math.cos(r) * 16} y2={50 + Math.sin(r) * 16}
          stroke="#00d4ff" strokeWidth="1" opacity="0.5" />
      })}
      {/* centre dot */}
      <circle cx="50" cy="50" r="5" fill="url(#gc)" filter="url(#gl)"
        className="center-dot" />
    </svg>
  )
}

/* ── Ripple rings ─────────────────────────────────────────── */
function Ripples({ active }) {
  if (!active) return null
  return (
    <div className="fab-ripples">
      <span style={{ animationDelay: '0s' }} />
      <span style={{ animationDelay: '0.5s' }} />
      <span style={{ animationDelay: '1s' }} />
    </div>
  )
}

/* ── Waveform bars ────────────────────────────────────────── */
function WaveBars({ active }) {
  if (!active) return null
  return (
    <div className="wave-bars">
      {Array.from({ length: 12 }, (_, i) => (
        <span key={i} style={{ animationDelay: `${(i * 0.04).toFixed(2)}s`,
          '--h': 0.2 + Math.sin((i / 11) * Math.PI) * 0.8 }} />
      ))}
    </div>
  )
}

/* ── Chat bubble ──────────────────────────────────────────── */
function Bubble({ label, text }) {
  if (!text) return null
  return (
    <div className="bubble">
      <span className="bubble-label">{label}</span>
      <p className="bubble-text">{text}</p>
    </div>
  )
}

/* ═════════════════════════════════════════════════════════════
   ROOT APP — floating widget
═════════════════════════════════════════════════════════════ */
export default function App() {
  const [state, setState]       = useState('standby')
  const [expanded, setExpanded] = useState(false)
  const [transcript, setTx]    = useState('')
  const [response, setRx]      = useState('')
  const [connected, setOnline] = useState(false)
  const wsRef    = useRef(null)
  const timerRef = useRef(null)
  const panelRef = useRef(null)

  /* ── drag state ── */
  const [pos, setPos]     = useState({ x: 24, y: 24 })
  const dragRef           = useRef(null)

  const onPointerDown = useCallback((e) => {
    e.preventDefault()
    dragRef.current = { sx: e.clientX - pos.x, sy: e.clientY - pos.y }
    document.addEventListener('pointermove', onPointerMove)
    document.addEventListener('pointerup', onPointerUp)
  }, [pos])

  const onPointerMove = useCallback((e) => {
    if (!dragRef.current) return
    setPos({ x: e.clientX - dragRef.current.sx, y: e.clientY - dragRef.current.sy })
  }, [])

  const onPointerUp = useCallback(() => {
    dragRef.current = null
    document.removeEventListener('pointermove', onPointerMove)
    document.removeEventListener('pointerup', onPointerUp)
  }, [onPointerMove])

  /* ── WebSocket ── */
  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(`ws://${window.location.host}/ws`)
      wsRef.current = ws
      ws.onopen  = () => setOnline(true)
      ws.onclose = () => { setOnline(false); timerRef.current = setTimeout(connect, 2000) }
      ws.onerror = () => ws.close()

      ws.onmessage = ({ data }) => {
        const ev = JSON.parse(data)
        switch (ev.type) {
          case 'wake':
            setExpanded(true); setTx(''); setRx(''); setState('wake')
            break
          case 'listening':
            setState('listening')
            break
          case 'transcript':
            setTx(ev.text); setState('thinking')
            break
          case 'response':
            setRx(ev.text); setState('speaking')
            break
          case 'done':
            setState('listening')
            break
          case 'standby':
            setState('standby')
            timerRef.current = setTimeout(() => setExpanded(false), 2000)
            break
          default: break
        }
      }
    }
    connect()
    return () => { clearTimeout(timerRef.current); wsRef.current?.close() }
  }, [])

  /* auto-scroll panel */
  useEffect(() => {
    panelRef.current?.scrollTo({ top: panelRef.current.scrollHeight, behavior: 'smooth' })
  }, [transcript, response])

  const isActive   = state !== 'standby'
  const showPanel  = expanded && (transcript || response || isActive)

  return (
    <div
      className={`jarvis-widget state-${state}`}
      style={{ left: pos.x, bottom: pos.y }}
    >
      {/* ── Floating Action Button ── */}
      <div
        className={`fab${isActive ? ' active' : ''}${connected ? '' : ' offline'}`}
        onPointerDown={onPointerDown}
        title={connected ? STATUS[state] : 'OFFLINE'}
      >
        <Ripples active={state === 'listening'} />
        <MiniOrb state={state} />
        <WaveBars active={state === 'speaking'} />
        {!connected && <div className="fab-offline-dot" />}
      </div>

      {/* ── Status badge ── */}
      {isActive && (
        <div className="status-badge">{STATUS[state]}</div>
      )}

      {/* ── Expanded chat panel ── */}
      {showPanel && (
        <div className="chat-panel" ref={panelRef}>
          <div className="chat-header">
            <span className="chat-title">J.A.R.V.I.S</span>
            <span className={`chat-dot ${connected ? 'on' : 'off'}`} />
          </div>
          <div className="chat-body">
            <Bubble label="YOU" text={transcript} />
            <Bubble label="JARVIS" text={response} />
            {state === 'thinking' && (
              <div className="thinking-dots">
                <span /><span /><span />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

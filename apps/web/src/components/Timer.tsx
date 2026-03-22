import { useState, useEffect, useRef } from 'react'

interface TimerProps {
  expiresAt: string
  onExpire: () => void
}

const styles = {
  timer: {
    fontFamily: "'Press Start 2P', monospace",
    fontSize: '0.9rem',
    padding: '8px 16px',
    borderRadius: 4,
    border: '1px solid rgba(0,255,65,0.2)',
    background: 'rgba(0,15,0,0.6)',
  },
  normal: {
    color: '#00ff41',
    textShadow: '0 0 10px rgba(0,255,65,0.3)',
  },
  warning: {
    color: '#ffaa00',
    textShadow: '0 0 10px rgba(255,170,0,0.4)',
    animation: 'pulse 1s ease-in-out infinite',
  },
  critical: {
    color: '#ff4444',
    textShadow: '0 0 15px rgba(255,68,68,0.5)',
    animation: 'pulse 0.5s ease-in-out infinite',
  },
}

function formatTime(seconds: number): string {
  if (seconds <= 0) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

export default function Timer({ expiresAt, onExpire }: TimerProps) {
  const [secondsLeft, setSecondsLeft] = useState(() => {
    const diff = Math.floor((new Date(expiresAt).getTime() - Date.now()) / 1000)
    return Math.max(0, diff)
  })
  const expiredRef = useRef(false)

  useEffect(() => {
    const interval = setInterval(() => {
      const diff = Math.floor((new Date(expiresAt).getTime() - Date.now()) / 1000)
      const remaining = Math.max(0, diff)
      setSecondsLeft(remaining)

      if (remaining <= 0 && !expiredRef.current) {
        expiredRef.current = true
        onExpire()
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [expiresAt, onExpire])

  const timerStyle = secondsLeft <= 60
    ? styles.critical
    : secondsLeft <= 180
      ? styles.warning
      : styles.normal

  return (
    <>
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
      <div style={{ ...styles.timer, ...timerStyle }}>
        {formatTime(secondsLeft)}
      </div>
    </>
  )
}

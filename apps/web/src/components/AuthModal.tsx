import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

interface AuthModalProps {
  isOpen: boolean
  onClose: () => void
  mode: 'signin' | 'signup'
  intent?: 'dashboard' | 'premium_assessment'
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path fill="#EA4335" d="M12 10.2v3.9h5.4c-.2 1.3-1.6 3.9-5.4 3.9-3.3 0-5.9-2.7-5.9-6s2.6-6 5.9-6c1.9 0 3.2.8 3.9 1.5l2.7-2.6C17 3.5 14.8 2.5 12 2.5A9.5 9.5 0 0 0 2.5 12 9.5 9.5 0 0 0 12 21.5c5.5 0 9.1-3.9 9.1-9.3 0-.6-.1-1.1-.2-1.6H12Z" />
      <path fill="#4285F4" d="M3.6 7.6 6.8 10c.9-2.7 3.3-4.5 6-4.5 1.9 0 3.2.8 3.9 1.5l2.7-2.6C17 3.5 14.8 2.5 12 2.5 8.4 2.5 5.3 4.5 3.6 7.6Z" />
      <path fill="#FBBC05" d="M2.5 12c0 1.5.4 3 1.1 4.3l3.7-2.9c-.2-.5-.3-.9-.3-1.4s.1-1 .3-1.4L3.6 7.6A9.4 9.4 0 0 0 2.5 12Z" />
      <path fill="#34A853" d="M12 21.5c2.7 0 5-.9 6.7-2.5l-3.3-2.7c-.9.7-2 1.2-3.4 1.2-2.7 0-5.1-1.8-5.9-4.3l-3.8 2.9c1.7 3.2 5 5.4 9.7 5.4Z" />
    </svg>
  )
}

function GitHubIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M12 .5C5.6.5.5 5.7.5 12.2c0 5.2 3.4 9.5 8.1 11.1.6.1.8-.3.8-.6v-2.2c-3.3.7-4-1.6-4-1.6-.5-1.4-1.3-1.8-1.3-1.8-1.1-.8.1-.8.1-.8 1.2.1 1.9 1.3 1.9 1.3 1.1 1.9 2.8 1.4 3.5 1.1.1-.8.4-1.4.8-1.8-2.7-.3-5.6-1.4-5.6-6.2 0-1.4.5-2.5 1.3-3.4-.1-.3-.6-1.6.1-3.3 0 0 1.1-.4 3.5 1.3 1-.3 2.1-.4 3.1-.4s2.1.1 3.1.4c2.4-1.7 3.5-1.3 3.5-1.3.7 1.7.2 3 .1 3.3.8.9 1.3 2 1.3 3.4 0 4.8-2.9 5.9-5.7 6.2.5.4.9 1.2.9 2.4v3.5c0 .3.2.7.8.6 4.7-1.6 8.1-5.9 8.1-11.1C23.5 5.7 18.4.5 12 .5Z"
      />
    </svg>
  )
}

export default function AuthModal({ isOpen, onClose, mode: initialMode, intent = 'dashboard' }: AuthModalProps) {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [mode, setMode] = useState(initialMode)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [message, setMessage] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  useEffect(() => {
    if (!isOpen) return
    setMode(initialMode)
    setShowPassword(false)
    setMessage('')
  }, [initialMode, isOpen])

  if (!isOpen) return null

  const handleOAuth = (provider: 'google' | 'github') => {
    sessionStorage.setItem('oauth_provider', provider)
    sessionStorage.setItem('auth_intent', intent)
    window.location.href = `${API_URL}/auth/${provider}`
  }

  const handleMagicLink = async () => {
    try {
      const res = await fetch(`${API_URL}/auth/magic-link`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })
      if (res.ok) {
        setMessage('Check your email for the login link')
      }
    } catch {
      setMessage('Failed to send magic link')
    }
  }

  const handlePasswordAuth = async () => {
    const endpoint = mode === 'signup' ? '/auth/register' : '/auth/login'
    const body = mode === 'signup' ? { email, name, password } : { email, password }

    try {
      const res = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      const data = await res.json().catch(() => null)

      if (!res.ok || !data?.token) {
        setMessage(data?.detail || 'Authentication failed')
        return
      }

      login(data.token, {
        id: data.id,
        email: data.email,
        name: data.name,
        avatar_url: data.avatar_url,
      })

      sessionStorage.setItem('auth_intent', intent)
      onClose()
      navigate(intent === 'dashboard' ? '/dashboard' : '/')
    } catch {
      setMessage('Authentication failed')
    }
  }

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
        <button style={styles.close} onClick={onClose}>×</button>

        <div style={styles.tabs}>
          <button
            style={mode === 'signin' ? styles.tabActive : styles.tab}
            onClick={() => setMode('signin')}
          >
            Sign In
          </button>
          <button
            style={mode === 'signup' ? styles.tabActive : styles.tab}
            onClick={() => setMode('signup')}
          >
            Sign Up
          </button>
        </div>

        <div style={styles.content}>
          <button style={styles.oauthBtn} onClick={() => handleOAuth('google')}>
            <span style={styles.oauthBtnContent}>
              <GoogleIcon />
              <span>Continue with Google</span>
            </span>
          </button>
          <button style={styles.oauthBtn} onClick={() => handleOAuth('github')}>
            <span style={styles.oauthBtnContent}>
              <GitHubIcon />
              <span>Continue with GitHub</span>
            </span>
          </button>

          <div style={styles.divider}>or</div>

          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={styles.input}
          />
          <button style={styles.magicBtn} onClick={handleMagicLink}>
            Send Magic Link
          </button>

          <div style={styles.divider}>or use password</div>

          {showPassword ? (
            <>
              {mode === 'signup' && (
                <input
                  type="text"
                  placeholder="Name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  style={styles.input}
                />
              )}
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={styles.input}
              />
              <button style={styles.submitBtn} onClick={handlePasswordAuth}>
                {mode === 'signin' ? 'Sign In' : 'Sign Up'}
              </button>
            </>
          ) : (
            <button style={styles.linkBtn} onClick={() => setShowPassword(true)}>
              Use password instead
            </button>
          )}

          {message && <p style={styles.message}>{message}</p>}
        </div>
      </div>
    </div>
  )
}

const styles = {
  overlay: {
    position: 'fixed' as const,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0,0,0,0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  modal: {
    background: 'white',
    borderRadius: '8px',
    width: '400px',
    maxWidth: '90%',
    position: 'relative' as const,
  },
  close: {
    position: 'absolute' as const,
    top: '10px',
    right: '10px',
    background: 'none',
    border: 'none',
    fontSize: '24px',
    cursor: 'pointer',
  },
  tabs: {
    display: 'flex',
    borderBottom: '1px solid #ddd',
  },
  tab: {
    flex: 1,
    padding: '15px',
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    fontSize: '16px',
  },
  tabActive: {
    flex: 1,
    padding: '15px',
    background: 'none',
    border: 'none',
    borderBottom: '2px solid #007bff',
    cursor: 'pointer',
    fontSize: '16px',
    fontWeight: 'bold' as const,
  },
  content: {
    padding: '20px',
  },
  oauthBtn: {
    width: '100%',
    padding: '12px',
    marginBottom: '10px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    background: 'white',
    cursor: 'pointer',
    fontSize: '14px',
  },
  oauthBtnContent: {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '10px',
  },
  divider: {
    textAlign: 'center' as const,
    margin: '15px 0',
    color: '#666',
    fontSize: '14px',
  },
  input: {
    width: '100%',
    padding: '12px',
    marginBottom: '10px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '14px',
    boxSizing: 'border-box' as const,
  },
  magicBtn: {
    width: '100%',
    padding: '12px',
    marginBottom: '10px',
    border: 'none',
    borderRadius: '4px',
    background: '#28a745',
    color: 'white',
    cursor: 'pointer',
    fontSize: '14px',
  },
  submitBtn: {
    width: '100%',
    padding: '12px',
    border: 'none',
    borderRadius: '4px',
    background: '#007bff',
    color: 'white',
    cursor: 'pointer',
    fontSize: '14px',
  },
  linkBtn: {
    width: '100%',
    padding: '12px',
    background: 'none',
    border: 'none',
    color: '#007bff',
    cursor: 'pointer',
    fontSize: '14px',
  },
  message: {
    marginTop: '10px',
    textAlign: 'center' as const,
    color: '#666',
    fontSize: '14px',
  },
}

import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function AuthCallback() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { login } = useAuth()
  const [error, setError] = useState('')
  const hasStarted = useRef(false)

  useEffect(() => {
    if (hasStarted.current) return
    hasStarted.current = true

    const code = searchParams.get('code')
    const authIntent = sessionStorage.getItem('auth_intent')
    const provider = sessionStorage.getItem('oauth_provider')

    if (!code) {
      sessionStorage.removeItem('oauth_provider')
      sessionStorage.removeItem('auth_intent')
      setError('No authorization code received')
      return
    }

    if (provider !== 'google' && provider !== 'github') {
      sessionStorage.removeItem('oauth_provider')
      sessionStorage.removeItem('auth_intent')
      setError('Authentication provider is missing')
      return
    }

    sessionStorage.removeItem('oauth_provider')

    fetch(`${API_URL}/auth/${provider}/callback?code=${encodeURIComponent(code)}`)
      .then(async (res) => {
        const data = await res.json().catch(() => null)
        if (!res.ok || !data?.token) {
          throw new Error(data?.detail || 'Authentication failed')
        }

        login(data.token, {
          id: data.id,
          email: data.email,
          name: data.name,
          avatar_url: data.avatar_url,
        })

        if (authIntent === 'dashboard') {
          sessionStorage.removeItem('auth_intent')
          navigate('/dashboard')
          return
        }

        if (authIntent === 'premium_assessment') {
          navigate('/')
          return
        }

        sessionStorage.removeItem('auth_intent')
        navigate('/')
      })
      .catch((err: unknown) => {
        sessionStorage.removeItem('auth_intent')
        const message = err instanceof Error ? err.message : 'Authentication failed'
        setError(message)
      })
  }, [login, navigate, searchParams])

  return (
    <div style={styles.container}>
      {error ? <p style={styles.error}>{error}</p> : <p>Authenticating...</p>}
    </div>
  )
}

const styles = {
  container: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100vh',
    fontSize: '18px',
  },
  error: {
    color: 'red',
  },
}

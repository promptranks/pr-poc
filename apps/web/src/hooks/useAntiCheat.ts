/**
 * useAntiCheat hook: monitors tab visibility changes and reports violations to backend.
 * Uses the Page Visibility API.
 */

import { useState, useEffect, useCallback, useRef } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface UseAntiCheatOptions {
  assessmentId: string
  enabled?: boolean
  maxViolations?: number
}

interface UseAntiCheatReturn {
  violations: number
  isVoided: boolean
  showWarning: boolean
  dismissWarning: () => void
}

export default function useAntiCheat({
  assessmentId,
  enabled = true,
  maxViolations: _maxViolations = 3,
}: UseAntiCheatOptions): UseAntiCheatReturn {
  const [violations, setViolations] = useState(0)
  const [isVoided, setIsVoided] = useState(false)
  const [showWarning, setShowWarning] = useState(false)
  const reportingRef = useRef(false)

  const reportViolation = useCallback(
    async (violationType: string) => {
      if (reportingRef.current || isVoided) return
      reportingRef.current = true

      try {
        const res = await fetch(
          `${API_URL}/assessments/${assessmentId}/violation`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ violation_type: violationType }),
          }
        )
        if (res.ok) {
          const data = await res.json()
          setViolations(data.violations)
          if (data.voided) {
            setIsVoided(true)
          }
        }
      } catch {
        // Silently fail — don't block assessment
      } finally {
        reportingRef.current = false
      }
    },
    [assessmentId, isVoided]
  )

  const dismissWarning = useCallback(() => {
    setShowWarning(false)
  }, [])

  useEffect(() => {
    if (!enabled) return

    const handleVisibilityChange = () => {
      if (document.hidden) {
        setShowWarning(true)
        reportViolation('tab_switch')
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [enabled, reportViolation])

  return {
    violations,
    isVoided,
    showWarning,
    dismissWarning,
  }
}

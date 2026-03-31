/**
 * Session ID utility for anonymous user state management
 * Generates and persists a unique session ID in localStorage
 */

const SESSION_ID_KEY = 'prk_session_id';

/**
 * Generate a random session ID
 */
function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`;
}

/**
 * Get existing session ID or create a new one
 */
export function getOrCreateSessionId(): string {
  let sessionId = localStorage.getItem(SESSION_ID_KEY);

  if (!sessionId) {
    sessionId = generateSessionId();
    localStorage.setItem(SESSION_ID_KEY, sessionId);
  }

  return sessionId;
}

/**
 * Get existing session ID without creating a new one
 */
export function getSessionId(): string | null {
  return localStorage.getItem(SESSION_ID_KEY);
}

/**
 * Clear session ID (useful for logout or reset)
 */
export function clearSessionId(): void {
  localStorage.removeItem(SESSION_ID_KEY);
}

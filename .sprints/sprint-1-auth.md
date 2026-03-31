# Sprint 1: Auth Foundation

**Duration:** 5 days
**Goal:** Implement OAuth + Magic Link authentication
**Status:** Ready

---

## Database Migrations

### Migration 001: OAuth Accounts
```sql
CREATE TABLE oauth_accounts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  provider VARCHAR(50) NOT NULL,
  provider_user_id VARCHAR(255) NOT NULL,
  access_token TEXT,
  refresh_token TEXT,
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(provider, provider_user_id)
);
CREATE INDEX idx_oauth_user ON oauth_accounts(user_id);
```

### Migration 002: Magic Links
```sql
CREATE TABLE magic_links (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email VARCHAR(255) NOT NULL,
  token VARCHAR(255) UNIQUE NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  used_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_magic_token ON magic_links(token);
CREATE INDEX idx_magic_email ON magic_links(email);
```

### Migration 003: User OAuth Fields
```sql
ALTER TABLE users ADD COLUMN avatar_url TEXT;
ALTER TABLE users ADD COLUMN oauth_provider VARCHAR(50);
```

---

## Backend Tasks

### Task 1.1: OAuth Models
**File:** `apps/api/app/models/oauth_account.py`
- OAuthAccount model
- Relationships to User

### Task 1.2: Magic Link Model
**File:** `apps/api/app/models/magic_link.py`
- MagicLink model
- Token generation utility

### Task 1.3: Google OAuth Service
**File:** `apps/api/app/services/google_oauth.py`
- Get authorization URL
- Exchange code for tokens
- Get user info from Google

### Task 1.4: GitHub OAuth Service
**File:** `apps/api/app/services/github_oauth.py`
- Get authorization URL
- Exchange code for tokens
- Get user info from GitHub

### Task 1.5: Magic Link Service
**File:** `apps/api/app/services/magic_link.py`
- Generate magic link
- Send email
- Verify token
- Mark as used

### Task 1.6: OAuth Router
**File:** `apps/api/app/routers/oauth.py`
- GET /auth/google
- GET /auth/google/callback
- GET /auth/github
- GET /auth/github/callback

### Task 1.7: Magic Link Router
**File:** `apps/api/app/routers/magic_link.py`
- POST /auth/magic-link
- GET /auth/magic-link/verify

---

## Frontend Tasks

### Task 1.8: Auth Context
**File:** `apps/web/src/contexts/AuthContext.tsx`
- Auth state management
- Login/logout functions
- Token storage

### Task 1.9: AuthModal Component
**File:** `apps/web/src/components/AuthModal.tsx`
- Sign In/Sign Up tabs
- OAuth buttons (Google, GitHub)
- Magic link form
- Email/password fallback

### Task 1.10: Update Landing Page
**File:** `apps/web/src/pages/Landing.tsx`
- Add auth links below CTA buttons
- Integrate AuthModal

### Task 1.11: OAuth Callback Handler
**File:** `apps/web/src/pages/AuthCallback.tsx`
- Handle OAuth redirects
- Extract tokens
- Redirect to dashboard

### Task 1.12: Magic Link Verify Page
**File:** `apps/web/src/pages/MagicLinkVerify.tsx`
- Verify token from URL
- Auto-login
- Redirect to dashboard

---

## Testing Checklist

- [ ] Google OAuth flow works end-to-end
- [ ] GitHub OAuth flow works end-to-end
- [ ] Magic link email sent and verified
- [ ] Existing email/password auth still works
- [ ] User profile shows OAuth provider
- [ ] Avatar from OAuth displayed
- [ ] Token refresh works
- [ ] Error handling for expired tokens
- [ ] Rate limiting on magic link endpoint

---

## Dependencies

**Backend:**
- authlib (OAuth library)
- python-jose (JWT)
- sendgrid or postmark (email)

**Frontend:**
- None (use fetch API)

---

## Deliverables

✅ Users can sign in with Google
✅ Users can sign in with GitHub
✅ Users can sign in with magic link
✅ Auth modal integrated on landing
✅ OAuth avatars displayed

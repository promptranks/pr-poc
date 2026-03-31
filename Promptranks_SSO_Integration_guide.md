# Promptranks SSO Integration Guide

This guide explains how to configure Google and GitHub SSO for PromptRanks using the existing backend OAuth implementation.

## 1. What the current code already supports

The backend already supports:
- Google OAuth
- GitHub OAuth
- OAuth callback token exchange
- automatic user creation/login

Relevant backend config fields:
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GITHUB_CLIENT_ID`
- `GITHUB_CLIENT_SECRET`
- `OAUTH_REDIRECT_URL`

Backend files already wired for this:
- `apps/api/app/config.py`
- `apps/api/app/routers/auth.py`
- `apps/api/app/services/oauth_service.py`

Frontend files already wired for this:
- `apps/web/src/components/AuthModal.tsx`
- `apps/web/src/pages/AuthCallback.tsx`

## 2. Important implementation detail

The current frontend callback page is:
- `/auth/callback`

The backend currently exposes provider-specific callback endpoints:
- `/auth/google/callback`
- `/auth/github/callback`

That means your OAuth app/provider settings must send the user back to the frontend callback route, and the frontend must know which provider is being completed.

## 3. Required environment variables

Add these values to your PromptRanks `.env` file.

```env
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
OAUTH_REDIRECT_URL=https://prk.promptranks.org/auth/callback
```

For local development:

```env
OAUTH_REDIRECT_URL=http://localhost:3000/auth/callback
```

If you run the frontend on Vite default local port instead of Docker web on 3000, use:

```env
OAUTH_REDIRECT_URL=http://localhost:5173/auth/callback
```

## 4. Google SSO setup

### 4.1 Create the Google OAuth app
1. Open Google Cloud Console.
2. Select or create a project for PromptRanks.
3. Go to **APIs & Services** → **Credentials**.
4. Click **Create Credentials** → **OAuth client ID**.
5. If prompted, configure the OAuth consent screen first.

### 4.2 Configure the consent screen
Use the values that match your deployment.

Recommended basics:
- App name: `PromptRanks`
- User support email: your support/admin email
- Developer contact email: your admin email

Scopes currently needed by the backend:
- `openid`
- `email`
- `profile`

### 4.3 Configure redirect URIs
Add the frontend callback URL you actually use.

Production:
- `https://prk.promptranks.org/auth/callback`

Local Docker frontend:
- `http://localhost:3000/auth/callback`

Local Vite frontend:
- `http://localhost:5173/auth/callback`

### 4.4 Copy credentials
After Google creates the OAuth client:
- copy the **Client ID** into `GOOGLE_CLIENT_ID`
- copy the **Client Secret** into `GOOGLE_CLIENT_SECRET`

## 5. GitHub SSO setup

### 5.1 Create the GitHub OAuth app
1. Open GitHub.
2. Go to **Settings** → **Developer settings** → **OAuth Apps**.
3. Click **New OAuth App**.

### 5.2 Configure the GitHub OAuth app
Recommended values:
- Application name: `PromptRanks`
- Homepage URL: `https://prk.promptranks.org`
- Authorization callback URL: `https://prk.promptranks.org/auth/callback`

For local development, create a separate local OAuth app or temporarily switch the callback URL to:
- `http://localhost:3000/auth/callback`
- or `http://localhost:5173/auth/callback`

### 5.3 Copy credentials
After GitHub creates the app:
- copy the **Client ID** into `GITHUB_CLIENT_ID`
- generate/copy the **Client Secret** into `GITHUB_CLIENT_SECRET`

## 6. Update your `.env`

Example production configuration:

```env
GOOGLE_CLIENT_ID=xxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxx
GITHUB_CLIENT_ID=Iv1.xxxxxxxxxxxxxxxx
GITHUB_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OAUTH_REDIRECT_URL=https://prk.promptranks.org/auth/callback
```

Example local configuration:

```env
GOOGLE_CLIENT_ID=xxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxx
GITHUB_CLIENT_ID=Iv1.xxxxxxxxxxxxxxxx
GITHUB_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OAUTH_REDIRECT_URL=http://localhost:3000/auth/callback
```

## 7. Rebuild / restart after config changes

After updating `.env`, rebuild or restart the containers that use these values.

Typical stack commands from the canonical repo path:

```bash
docker compose -f /Volumes/DEV/Scopelabs.work/opensource/prk-poc/docker-compose.yml --project-directory /Volumes/DEV/Scopelabs.work/opensource/prk-poc up -d --build api web
```

Use `/Volumes/...`, not `/volumes/...`.

## 8. Validation checklist

### Google
1. Open PromptRanks.
2. Open the sign-in/sign-up modal.
3. Click **Continue with Google**.
4. Complete Google sign-in.
5. Confirm you return to PromptRanks.
6. Confirm the user is logged in.

### GitHub
1. Open PromptRanks.
2. Open the sign-in/sign-up modal.
3. Click **Continue with GitHub**.
4. Complete GitHub sign-in.
5. Confirm you return to PromptRanks.
6. Confirm the user is logged in.

## 9. What to check if SSO fails

### Error: redirect_uri_mismatch
Cause:
- the callback URL configured in Google/GitHub does not exactly match `OAUTH_REDIRECT_URL`

Fix:
- make them exactly identical, including protocol, hostname, port, and path

### Error: backend missing client ID/secret
Cause:
- one or more OAuth env vars are empty inside the API container

Fix:
- verify `.env`
- rebuild/restart `api`
- verify container env values

### Error: frontend returns but user is not logged in
Cause:
- callback flow mismatch between provider callback URL and frontend/backend expectations

Fix:
- verify the browser returns to `/auth/callback`
- verify the callback page receives `code`
- verify frontend then calls the backend callback endpoint for the correct provider

### Error: account created but avatar missing
Cause:
- database schema drift on `users.avatar_url`

Fix:
- ensure the `users` table includes:
  - `avatar_url`
  - `oauth_provider`

## 10. Recommended production values

Production frontend:
- `https://prk.promptranks.org`

Production API:
- `https://api.promptranks.org`

Recommended production OAuth redirect:
- `https://prk.promptranks.org/auth/callback`

## 11. Summary

You will need to provide:
- Google Client ID + Client Secret
- GitHub Client ID + Client Secret
- the exact redirect URL to use in this environment

Once those values are added to `.env` and the containers are restarted, the existing PromptRanks backend is already structured to support Google and GitHub SSO.

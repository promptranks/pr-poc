# PromptRanks PoC — Development Instructions

## Project Overview
Open-source AI prompt engineering assessment platform using the PECAM framework.
Tech stack: FastAPI + React/TypeScript + PostgreSQL + Redis + Claude API.

## Key Rules
- **Dual license**: Code is MIT, content (questions/tasks/docs) is CC-BY-SA 4.0
- **Security**: Never commit API keys, use .env for secrets, validate all user input
- **Bcrypt for passwords**: Use bcrypt directly (not Passlib), 72-byte limit
- **SHA256 for tokens**: JWT and session tokens use SHA256
- **Anti-cheat**: Assessment pages must enforce tab-lock and timer

## Architecture
- `apps/api/` — FastAPI backend (Python 3.12)
- `apps/web/` — React 18 + TypeScript + Vite frontend
- `content/` — KBA questions and PPA tasks in YAML (CC-BY-SA)
- `infra/` — Docker, Postgres schema, Nginx
- `scripts/` — Seed data, utilities

## Development
```bash
docker compose up -d          # Start all services
docker compose exec api pytest  # Run backend tests
cd apps/web && npm run dev    # Frontend dev server
```

## Conventions
- Python: ruff for linting, mypy for types
- TypeScript: ESLint + Prettier
- Commits: Conventional Commits (feat:, fix:, docs:, content:)
- Branches: feature/* from develop, squash-merge PRs
- Questions/tasks: YAML format in content/, follow existing examples

## Design System — Matrix Theme (v2)

All frontend pages MUST follow the PromptRanks v2 matrix/cyberpunk theme. Reference: https://v2.promptranks.org

### CSS Variables
```css
:root {
  /* Matrix greens */
  --matrix-green: #00ff41;
  --matrix-green-dim: #008f11;
  --matrix-green-glow: rgba(0,255,65,0.4);
  --matrix-green-subtle: rgba(0,255,65,0.08);
  --matrix-green-border: rgba(0,255,65,0.2);

  /* Backgrounds */
  --bg-page: #000000;
  --bg-card: rgba(0,15,0,0.6);
  --bg-card-hover: rgba(0,25,0,0.8);

  /* Text */
  --text-primary: #00ff41;
  --text-secondary: #008f11;
  --text-white: #c0ffc0;

  /* Borders & Shadows */
  --border: rgba(0,255,65,0.1);
  --border-hover: rgba(0,255,65,0.3);
  --shadow-glow: 0 0 30px rgba(0,255,65,0.3);
  --shadow-card: 0 8px 32px rgba(0,0,0,0.8);

  /* Radius */
  --radius: 4px;
  --radius-lg: 8px;
  --radius-xl: 12px;

  /* Fonts */
  --font-heading: 'Press Start 2P', monospace;
  --font-body: 'Share Tech Mono', monospace;

  /* Accent (for CTAs, badges, gradients) */
  --accent-purple: #6D5FFA;
  --accent-pink: #EC41FB;
  --gradient-cta: linear-gradient(135deg, #6D5FFA 0%, #8B5CF6 40%, #EC41FB 100%);
}
```

### Design Rules
- **Background**: Pure black (#000000) with optional matrix rain canvas
- **Cards**: Dark translucent green (`--bg-card`) with green border glow on hover
- **Text**: Matrix green for headings, light green (`--text-white: #c0ffc0`) for body
- **Fonts**: Monospace everywhere — `Share Tech Mono` for body, `Press Start 2P` for headings
- **Buttons/CTAs**: Purple-to-pink gradient (`--gradient-cta`) — same as the website
- **Glow effects**: Green glow on interactive elements (inputs, cards, buttons)
- **Scanlines**: Optional subtle scanline overlay for atmosphere
- **Icons/Badges**: Use matrix green accents, monospace labels
- **Assessment page**: Dark, focused, minimal — no distractions, terminal-like feel
- **Results page**: Score reveal with glow animation, radar chart in green
- **No bright whites** — use `#c0ffc0` instead of `#ffffff`


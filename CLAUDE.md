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

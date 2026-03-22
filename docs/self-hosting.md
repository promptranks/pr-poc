# Self-Hosting Guide

## Prerequisites

- Docker & Docker Compose v2+
- 2GB RAM minimum
- An Anthropic API key ([console.anthropic.com](https://console.anthropic.com/))

## Quick Start

```bash
git clone https://github.com/promptranks/pr-poc.git
cd pr-poc
cp .env.example .env
```

Edit `.env` and set:
- `ANTHROPIC_API_KEY` — your Claude API key
- `POSTGRES_PASSWORD` — change from default
- `SECRET_KEY` — generate with `openssl rand -hex 32`

```bash
docker compose up -d
docker compose exec api python scripts/seed-questions.py
```

Open `http://localhost:3000`.

## Services

| Service | Port | Purpose |
|---------|------|---------|
| Web (React) | 3000 | Frontend |
| API (FastAPI) | 8000 | Backend |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Sessions, cache |

## Environment Variables

See [.env.example](../.env.example) for all available configuration options.

### Required
- `ANTHROPIC_API_KEY` — Claude API key for PPA execution and judging
- `SECRET_KEY` — JWT signing key

### Optional
- `LLM_EXECUTOR_MODEL` — Model for running user prompts (default: `claude-sonnet-4-6`)
- `LLM_JUDGE_MODEL` — Model for scoring outputs (default: `claude-opus-4-6`)
- `QUICK_ASSESSMENT_TIME_LIMIT` — Quick mode timer in seconds (default: 900)

## Data Persistence

PostgreSQL data is stored in a Docker volume (`pr-poc-pgdata`). To back up:

```bash
docker compose exec postgres pg_dump -U promptranks promptranks > backup.sql
```

## Updating

```bash
git pull origin main
docker compose build
docker compose up -d
docker compose exec api python scripts/seed-questions.py
```

## Troubleshooting

**API won't start**: Check `docker compose logs api` — usually a missing env var.

**LLM calls fail**: Verify your `ANTHROPIC_API_KEY` is valid and has credits.

**Database errors**: Run `docker compose down -v` to reset (destroys data).

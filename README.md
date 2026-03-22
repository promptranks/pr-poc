# PromptRanks PoC

**Open-source AI prompt engineering assessment platform.**

Measure your AI prompting skill in 15 minutes. Get a verifiable badge. Share it with the world.

[![License: MIT](https://img.shields.io/badge/Code-MIT-blue.svg)](LICENSE)
[![License: CC BY-SA 4.0](https://img.shields.io/badge/Content-CC%20BY--SA%204.0-lightgrey.svg)](LICENSE-CONTENT)
[![CI](https://github.com/promptranks/pr-poc/actions/workflows/ci.yml/badge.svg)](https://github.com/promptranks/pr-poc/actions)

---

## What is PromptRanks?

PromptRanks assesses your AI prompting ability using the **PECAM framework** — five pillars that cover everything from basic prompt design to building autonomous agent systems.

| Pillar | Name | What It Measures |
|--------|------|------------------|
| **P** | Prompt Design | Clarity, structure, format control |
| **E** | Execution & Iteration | Testing, debugging, refinement |
| **C** | Context Management | Memory, RAG, multi-document handling |
| **M** | Meta-Cognition | Model understanding, bias awareness |
| **A** | Agentic Prompting | Multi-step pipelines, tool use, agents |

### Two Assessment Modes

| | Quick (15 min) | Full (~60 min) |
|---|---|---|
| KBA (Knowledge) | 10 questions | 20 questions |
| PPA (Practical) | 1 multi-pillar task | 3–5 tasks |
| PSV (Portfolio) | — | Portfolio submission |
| Result | Estimated Level | Certified Level |

### Five Proficiency Levels

| Level | Name | Score |
|-------|------|-------|
| L1 | Foundational | 0–49 |
| L2 | Practitioner | 50–69 |
| L3 | Proficient | 70–84 |
| L4 | Advanced | 85–94 |
| L5 | Master | 95–100 |

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- An Anthropic API key ([get one here](https://console.anthropic.com/))

### Run

```bash
# Clone
git clone https://github.com/promptranks/pr-poc.git
cd pr-poc

# Configure
cp .env.example .env
# Edit .env and set your ANTHROPIC_API_KEY

# Start
docker compose up -d

# Seed sample questions
docker compose exec api python scripts/seed-questions.py

# Open
open http://localhost:3000
```

### Development

```bash
# Backend (FastAPI)
cd apps/api
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (React + Vite)
cd apps/web
npm install
npm run dev
```

---

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  React SPA  │────▶│  FastAPI API  │────▶│  PostgreSQL 16  │
│  (Vite+TS)  │     │  (Python)     │     └─────────────────┘
└─────────────┘     │  ┌──────────┐ │
                    │  │ LLM      │ │────▶  Claude API
                    │  │ Executor │ │
                    │  └──────────┘ │     ┌─────────────┐
                    │  ┌──────────┐ │     │   Redis 7   │
                    │  │ Badge    │ │     │  (Sessions)  │
                    │  │ Service  │ │     └─────────────┘
                    │  └──────────┘ │
                    └──────────────┘
```

---

## Project Structure

```
pr-poc/
├── apps/
│   ├── api/          # FastAPI backend
│   └── web/          # React frontend
├── content/
│   ├── questions/    # KBA question bank (YAML)
│   └── tasks/        # PPA task definitions (YAML)
├── docs/             # Methodology, scoring, self-hosting
├── infra/            # Docker, Postgres, Nginx configs
└── scripts/          # Seed data, question generation
```

---

## Documentation

- [PECAM Methodology](docs/methodology.md) — The assessment framework
- [Scoring Algorithm](docs/scoring.md) — How scores are calculated
- [Self-Hosting Guide](docs/self-hosting.md) — Deploy your own instance
- [API Reference](docs/api.md) — REST API documentation
- [Contributing Questions](docs/contributing-questions.md) — Add to the question bank
- [Architecture](docs/architecture.md) — System design

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Ways to contribute:**
- Report bugs
- Add KBA questions or PPA tasks
- Improve scoring algorithms
- Add translations
- Improve documentation

---

## License

- **Code** (`apps/`, `infra/`, `scripts/`): [MIT License](LICENSE)
- **Content** (`content/`, `docs/`): [CC BY-SA 4.0](LICENSE-CONTENT)

---

## Links

- Website: [promptranks.org](https://promptranks.org)
- Methodology: [PECAM Framework](docs/methodology.md)

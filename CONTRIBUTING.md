# Contributing to PromptRanks

Thank you for your interest in contributing! This guide will help you get started.

## Ways to Contribute

| Type | Skill Level | License |
|------|------------|---------|
| Report bugs | Beginner | — |
| Fix typos/docs | Beginner | MIT / CC-BY-SA |
| Add KBA questions | Intermediate | CC-BY-SA |
| Add PPA tasks | Intermediate | CC-BY-SA |
| Improve scoring | Advanced | MIT |
| Add translations | Intermediate | CC-BY-SA |
| Methodology RFC | Expert | CC-BY-SA |

## Development Setup

```bash
# 1. Fork the repo on GitHub
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/pr-poc.git
cd pr-poc

# 3. Configure
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# 4. Start services
docker compose up -d

# 5. Seed data
docker compose exec api python scripts/seed-questions.py
```

## Branch Workflow

```
main      ← stable releases (protected)
└─ develop ← integration branch
    └─ feature/your-feature ← your work
```

1. Create a branch from `develop`: `git checkout -b feature/your-feature develop`
2. Make your changes
3. Run tests: `docker compose exec api pytest`
4. Push and open a PR targeting `develop`

## Adding KBA Questions

See [docs/contributing-questions.md](docs/contributing-questions.md) for the question format.

Questions go in `content/questions/pillar-X.yml`. Each question needs:
- Unique ID (e.g., `P-031`)
- Pillar tag (P, E, C, M, or A)
- Difficulty (1=easy, 2=medium, 3=hard)
- Exactly one correct answer (MCQ) or defined correct set (multi-select)
- Plausible distractors

## Adding PPA Tasks

Tasks go in `content/tasks/`. Each task needs:
- Title and brief
- Pillar tag
- Difficulty (1-3)
- Success criteria (list)
- Input data (if applicable)

## Code Standards

- **Python**: Ruff for linting, mypy for type checking
- **TypeScript**: ESLint + Prettier
- **Tests**: pytest (backend), Vitest (frontend)
- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `content:`)

## Pull Request Process

1. Ensure CI passes (lint, test, build)
2. Update documentation if needed
3. Add a changelog entry if user-facing
4. Request review from at least 1 maintainer
5. Squash-merge to develop

## Code of Conduct

Please read our [Code of Conduct](CODE_OF_CONDUCT.md). We are committed to providing a welcoming and inclusive experience.

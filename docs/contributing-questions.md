# Contributing Questions & Tasks

This guide explains how to add KBA questions or PPA tasks to PromptRanks.

## KBA Question Format

Questions are stored in `content/questions/pillar-X.yml` where X is the pillar letter (P, E, C, M, A).

### YAML Schema

```yaml
- id: "P-007"                    # Unique ID: pillar letter + sequential number
  difficulty: 2                   # 1=easy, 2=medium, 3=hard
  type: mcq                      # mcq, multi_select, true_false
  text: "Your question here?"    # The question text
  options:                        # 4 options for MCQ
    - "Option A"
    - "Option B"
    - "Option C"
    - "Option D"
  correct: 1                     # 0-indexed correct answer (or array for multi_select)
  explanation: "Why this is correct..."  # Required — shown after answering
  tags: ["topic1", "topic2"]     # Searchable tags
```

### Quality Rules

1. **Model-agnostic**: Never reference specific models ("What does GPT-4 do when..."). Use generic terms like "an LLM" or "a language model."
2. **One correct answer**: MCQ must have exactly one unambiguous correct answer.
3. **Plausible distractors**: Wrong options should be believable, not obviously wrong.
4. **Explanation required**: Every question must explain why the correct answer is right.
5. **Difficulty calibration**:
   - **Easy (1)**: Definition or basic concept recognition
   - **Medium (2)**: Application of a concept to a scenario
   - **Hard (3)**: Multi-step reasoning or nuanced judgment

### Pillar Distribution Target

Each pillar should have at least 6 questions (2 per difficulty level) for the PoC.

| Pillar | Current | Target (PoC) | Target (v1.0) |
|--------|---------|-------------|---------------|
| P | 6 | 6 | 100 |
| E | 6 | 6 | 80 |
| C | 6 | 6 | 100 |
| M | 6 | 6 | 60 |
| A | 6 | 6 | 60 |

## PPA Task Format

Tasks are stored in `content/tasks/task-*.yml`.

### YAML Schema

```yaml
task:
  id: "TASK-P-002"               # Unique ID
  title: "Task title"
  pillars_tested: ["P", "C"]     # Which pillars this task covers
  difficulty: 2                   # 1-3
  is_quick: false                 # true = eligible for Quick Assessment
  max_attempts: 3                 # How many times user can retry
  time_limit_seconds: 480         # Per-task time limit

  brief: |                        # Task instructions shown to user
    Describe what the user needs to do...

  input_data: |                   # Data provided to the user (optional)
    The document or data the user works with...

  success_criteria:               # List of measurable criteria
    - "Criterion 1"
    - "Criterion 2"

  scoring_rubric:                 # How LLM judge scores
    accuracy:
      weight: 0.30
      description: "..."
    completeness:
      weight: 0.25
      description: "..."
    prompt_efficiency:
      weight: 0.20
      description: "..."
    output_quality:
      weight: 0.15
      description: "..."
    creativity:
      weight: 0.10
      description: "..."
```

### Task Quality Rules

1. **Clear success criteria**: Must be measurable (not "write a good prompt")
2. **Realistic input data**: Use plausible scenarios, not contrived examples
3. **Multiple valid approaches**: No single "correct prompt" — different strategies should score differently but all can succeed
4. **Quick tasks**: Must touch 3+ pillars in a single task (multi-pillar design)

## Submission Process

1. Fork the repo
2. Add your question/task to the appropriate YAML file
3. Run `python3 scripts/seed-questions.py` to validate parsing
4. Submit a PR with the label `question-contribution`
5. Two reviewer approvals required for merge

## License

All contributed content is licensed under [CC BY-SA 4.0](../LICENSE-CONTENT). By submitting, you agree to this license.

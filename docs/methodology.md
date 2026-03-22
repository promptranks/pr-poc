# PECAM Methodology

For the complete PECAM methodology, see the [full document](https://github.com/promptranks/pr-poc/blob/main/../../PromptRanks_Methodology.md) or read below.

## Overview

PECAM is a competency model for AI prompt engineering. Every question, task, and evaluation criterion maps to one of five pillars.

## The Five Pillars

### P — Prompt Design
The ability to write clear, effective prompts that produce the intended output.
- Instruction clarity and specificity
- Output format control (JSON, markdown, tables, code)
- Constraint definition (length, tone, audience, exclusions)
- Role and persona framing
- Few-shot example construction
- Negative prompting

### E — Execution & Iteration
The ability to systematically refine prompts through testing and debugging.
- Identifying failure modes in outputs
- Systematic prompt debugging
- A/B comparison of prompt variants
- Prompt versioning and documentation
- Temperature and parameter tuning

### C — Context Management
The ability to manage information flow between user, prompt, and model.
- Context window awareness and optimization
- Document injection and summarization
- RAG patterns
- Conversation flow design (multi-turn)
- Memory strategies

### M — Meta-Cognition
The ability to understand model behavior, recognize limitations, and evaluate output quality.
- Understanding model capabilities and limitations
- Recognizing hallucinations and biases
- Calibrated confidence assessment
- Output verification strategies

### A — Agentic Prompting
The ability to design multi-step, autonomous prompt systems.
- Prompt chaining and pipeline design
- Tool use orchestration (function calling)
- Autonomous agent architecture
- Error handling in multi-step workflows

## Assessment Components

| Component | Weight | Format | Time |
|-----------|--------|--------|------|
| **KBA** (Knowledge) | 30% (full) / 40% (quick) | Multiple-choice | 15 min (full) / 5 min (quick) |
| **PPA** (Practical) | 60% | Prompt sandbox + LLM judge | 30 min (full) / 8 min (quick) |
| **PSV** (Portfolio) | 10% | Portfolio submission | 15 min (full only) |

## Proficiency Levels

| Level | Name | Score |
|-------|------|-------|
| L1 | Foundational | 0–49 |
| L2 | Practitioner | 50–69 |
| L3 | Proficient | 70–84 |
| L4 | Advanced | 85–94 |
| L5 | Master | 95–100 |

## License

This methodology is licensed under [CC BY-SA 4.0](../LICENSE-CONTENT).

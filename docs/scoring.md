# Scoring Algorithm

## Quick Assessment (15 minutes)

```
quick_score = (kba_score × 0.40) + (ppa_score × 0.60)
```

- **KBA score** = (correct_answers / 10) × 100
- **PPA score** = LLM judge score (0–100) on single multi-pillar task

## Full Assessment (~60 minutes)

```
full_score = (kba_score × 0.30) + (ppa_score × 0.60) + (psv_score × 0.10)
```

- **KBA score** = (correct_answers / 20) × 100
- **PPA score** = mean of all task scores (each 0–100)
- **PSV score** = LLM judge score on portfolio submission (0–100)

## Level Assignment

| Score Range | Level | Name |
|-------------|-------|------|
| 0–49 | L1 | Foundational |
| 50–69 | L2 | Practitioner |
| 70–84 | L3 | Proficient |
| 85–94 | L4 | Advanced |
| 95–100 | L5 | Master |

## PPA Task Scoring (LLM Judge)

Each PPA task is scored on 5 dimensions:

| Dimension | Weight | What It Measures |
|-----------|--------|------------------|
| Accuracy | 30% | Does the output correctly solve the task? |
| Completeness | 25% | Are all requirements addressed? |
| Prompt Efficiency | 20% | Was the prompt concise and well-structured? |
| Output Quality | 15% | Is the output well-formatted and professional? |
| Creativity | 10% | Novel approach or elegant solution? |

Task score = weighted sum of dimension scores.

## PECAM Radar Chart

Each badge includes per-pillar scores calculated from:
- KBA: questions tagged by pillar
- PPA: tasks tagged by pillar

```
pillar_score[X] = (kba_pillar_correct[X] / kba_pillar_total[X]) × 0.40
                + mean(ppa_task_scores where pillar == X) × 0.60
```

## License

This document is licensed under [CC BY-SA 4.0](../LICENSE-CONTENT).

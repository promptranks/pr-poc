"""PSV Engine: Portfolio/Self-Verification submission and LLM judging (full mode only)."""

import json
import logging
from typing import Any

import litellm

from app.config import settings

logger = logging.getLogger(__name__)


async def judge_psv_submission(
    submission_text: str,
    submission_url: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """Judge a PSV portfolio submission using LLM.

    Evaluates the submission on 3 dimensions:
    - relevance: How relevant is the portfolio to prompt engineering
    - depth: Depth of understanding demonstrated
    - evidence: Quality of supporting evidence/examples

    Returns: {"relevance": {"score": 80, "rationale": "..."}, ...}
    """
    target_model = model or settings.llm_judge_model

    context = f"Submission text:\n{submission_text}"
    if submission_url:
        context += f"\n\nPortfolio URL: {submission_url}"

    judge_prompt = f"""You are an expert evaluator for AI prompt engineering portfolio submissions.

Score the following portfolio/self-verification submission on exactly 3 dimensions.
Each score must be an integer from 0 to 100.

## Submission
{context}

## Scoring Dimensions

1. **relevance** (weight 0.40): How relevant is this submission to prompt engineering skills?
   Does it demonstrate real-world prompt engineering experience?

2. **depth** (weight 0.35): How deep is the understanding shown?
   Does the candidate explain techniques, reasoning, and tradeoffs?

3. **evidence** (weight 0.25): Quality of supporting evidence.
   Are there concrete examples, results, or artifacts?

## Instructions
Return ONLY a JSON object with this exact structure (no markdown, no explanation outside JSON):
{{
  "relevance": {{"score": <0-100>, "rationale": "<brief explanation>"}},
  "depth": {{"score": <0-100>, "rationale": "<brief explanation>"}},
  "evidence": {{"score": <0-100>, "rationale": "<brief explanation>"}}
}}"""

    response = await litellm.acompletion(
        model=target_model,
        max_tokens=1024,
        temperature=0.0,
        messages=[{"role": "user", "content": judge_prompt}],
    )

    raw_text: str = (response.choices[0].message.content or "").strip()  # type: ignore[union-attr]

    # Handle markdown code fences
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        json_lines: list[str] = []
        in_block = False
        for line in lines:
            if line.startswith("```") and not in_block:
                in_block = True
                continue
            if line.startswith("```") and in_block:
                break
            if in_block:
                json_lines.append(line)
        raw_text = "\n".join(json_lines)

    try:
        scores = json.loads(raw_text)
    except json.JSONDecodeError:
        logger.error("Failed to parse PSV judge response: %s", raw_text[:500])
        scores = {
            dim: {"score": 50, "rationale": "Judge response could not be parsed"}
            for dim in ["relevance", "depth", "evidence"]
        }

    # Validate and normalize
    dimensions = ["relevance", "depth", "evidence"]
    result: dict[str, Any] = {}
    for dim in dimensions:
        if dim in scores and isinstance(scores[dim], dict) and "score" in scores[dim]:
            score_val = max(0, min(100, int(scores[dim]["score"])))
            result[dim] = {
                "score": score_val,
                "rationale": scores[dim].get("rationale", ""),
            }
        else:
            result[dim] = {"score": 50, "rationale": "Dimension not evaluated"}

    return result


def compute_psv_score(judge_results: dict[str, Any]) -> float:
    """Compute weighted PSV score from judge dimensions.

    Weights: relevance=0.40, depth=0.35, evidence=0.25
    """
    weights = {
        "relevance": 0.40,
        "depth": 0.35,
        "evidence": 0.25,
    }

    total = 0.0
    for dim, weight in weights.items():
        dim_data = judge_results.get(dim, {})
        score = dim_data.get("score", 0) if isinstance(dim_data, dict) else 0
        total += weight * score

    return round(total, 1)

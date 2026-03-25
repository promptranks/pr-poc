"""Scoring service: final score computation, level assignment, PECAM pillar aggregation."""

from typing import Any

PILLARS = ["P", "E", "C", "A", "M"]

# Level boundaries (inclusive lower bounds)
LEVEL_BOUNDARIES: list[tuple[int, int, int]] = [
    # (level, min_score, max_score)
    (1, 0, 49),
    (2, 50, 69),
    (3, 70, 84),
    (4, 85, 94),
    (5, 95, 100),
]


def assign_level(score: float) -> int:
    """Assign proficiency level based on final score.

    L1: 0-49, L2: 50-69, L3: 70-84, L4: 85-94, L5: 95-100
    """
    rounded = round(score)
    if rounded >= 95:
        return 5
    if rounded >= 85:
        return 4
    if rounded >= 70:
        return 3
    if rounded >= 50:
        return 2
    return 1


def compute_final_score(
    mode: str,
    kba_score: float,
    ppa_score: float,
    psv_score: float | None = None,
) -> float:
    """Compute weighted final assessment score.

    Quick: KBA * 0.40 + PPA * 0.60
    Full:  KBA * 0.30 + PPA * 0.60 + PSV * 0.10
    """
    if mode == "quick":
        return round(kba_score * 0.40 + ppa_score * 0.60, 1)
    else:
        psv = psv_score if psv_score is not None else 0.0
        return round(kba_score * 0.30 + ppa_score * 0.60 + psv * 0.10, 1)


def aggregate_pillar_scores(
    kba_pillar_scores: dict[str, Any] | None,
    ppa_responses: dict[str, Any] | None,
) -> dict[str, dict[str, float]]:
    """Aggregate per-pillar scores across KBA + PPA.

    KBA contributes per-pillar correct % (already in kba_pillar_scores).
    PPA contributes per-pillar judge scores based on task.pillars_tested mapping.

    Returns: {"P": {"kba": 80.0, "ppa": 75.0, "combined": 77.0}, ...}
    """
    result: dict[str, dict[str, float]] = {}

    # Initialize with KBA scores
    for pillar in PILLARS:
        kba_val = 0.0
        if kba_pillar_scores and pillar in kba_pillar_scores:
            pillar_data = kba_pillar_scores[pillar]
            if isinstance(pillar_data, dict):
                kba_val = float(pillar_data.get("score", 0.0))
            else:
                kba_val = float(pillar_data)
        result[pillar] = {"kba": round(kba_val, 1), "ppa": 0.0, "combined": 0.0}

    # Extract PPA per-pillar scores from judge results
    if ppa_responses and "tasks" in ppa_responses:
        pillar_ppa_scores: dict[str, list[float]] = {p: [] for p in PILLARS}

        for _task_id, task_data in ppa_responses["tasks"].items():
            if not isinstance(task_data, dict):
                continue
            judge_result = task_data.get("judge_result")
            ppa_score = task_data.get("ppa_score")
            if judge_result is None or ppa_score is None:
                continue

            # Use pillars_tested if available in task brief, otherwise use task_data
            pillars_tested = task_data.get("pillars_tested")
            if not pillars_tested:
                # Default: attribute to all pillars equally
                pillars_tested = PILLARS

            for pillar in pillars_tested:
                if pillar in pillar_ppa_scores:
                    pillar_ppa_scores[pillar].append(float(ppa_score))

        for pillar in PILLARS:
            scores = pillar_ppa_scores[pillar]
            if scores:
                result[pillar]["ppa"] = round(sum(scores) / len(scores), 1)

    # Compute combined (average of KBA and PPA if both exist, otherwise whichever exists)
    for pillar in PILLARS:
        kba = result[pillar]["kba"]
        ppa = result[pillar]["ppa"]
        has_kba = kba_pillar_scores is not None and pillar in (kba_pillar_scores or {})
        has_ppa = ppa > 0

        if has_kba and has_ppa:
            result[pillar]["combined"] = round((kba + ppa) / 2, 1)
        elif has_kba:
            result[pillar]["combined"] = kba
        elif has_ppa:
            result[pillar]["combined"] = ppa
        else:
            result[pillar]["combined"] = 0.0

    return result

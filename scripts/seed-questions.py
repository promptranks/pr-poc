#!/usr/bin/env python3
"""Seed KBA questions and PPA tasks from YAML files into the database."""

import os
import sys
import yaml
import asyncio
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def load_questions(content_dir: str) -> list[dict]:
    """Load all question YAML files."""
    questions = []
    questions_dir = Path(content_dir) / "questions"
    for yml_file in sorted(questions_dir.glob("pillar-*.yml")):
        with open(yml_file) as f:
            data = yaml.safe_load(f)
        pillar = data["metadata"]["pillar"]
        for q in data["questions"]:
            questions.append({
                "external_id": q["id"],
                "pillar": pillar,
                "difficulty": q["difficulty"],
                "question_type": q.get("type", "mcq"),
                "question_text": q["text"],
                "options": q["options"],
                "correct_answer": q["correct"],
                "explanation": q.get("explanation", ""),
                "tags": q.get("tags", []),
            })
    return questions


def load_tasks(content_dir: str) -> list[dict]:
    """Load all task YAML files."""
    tasks = []
    tasks_dir = Path(content_dir) / "tasks"
    for yml_file in sorted(tasks_dir.glob("task-*.yml")):
        with open(yml_file) as f:
            data = yaml.safe_load(f)
        t = data["task"]
        tasks.append({
            "external_id": t["id"],
            "title": t["title"],
            "pillar": t["pillars_tested"][0],
            "pillars_tested": t["pillars_tested"],
            "difficulty": t["difficulty"],
            "brief": t["brief"],
            "input_data": t.get("input_data", ""),
            "success_criteria": t["success_criteria"],
            "scoring_rubric": t.get("scoring_rubric"),
            "max_attempts": t.get("max_attempts", 3),
            "time_limit_seconds": t.get("time_limit_seconds", 480),
            "is_quick": t.get("is_quick", False),
        })
    return tasks


def main():
    content_dir = os.environ.get("CONTENT_DIR", "/app/content")
    if not Path(content_dir).exists():
        # Local development: scripts/ is one level deep from repo root
        content_dir = str(Path(__file__).resolve().parent.parent / "content")

    questions = load_questions(content_dir)
    tasks = load_tasks(content_dir)

    print(f"Loaded {len(questions)} questions from {len(set(q['pillar'] for q in questions))} pillars")
    print(f"Loaded {len(tasks)} tasks ({sum(1 for t in tasks if t['is_quick'])} quick, {sum(1 for t in tasks if not t['is_quick'])} full)")

    for q in questions:
        print(f"  [{q['pillar']}-D{q['difficulty']}] {q['external_id']}: {q['question_text'][:60]}...")

    for t in tasks:
        print(f"  [{'QUICK' if t['is_quick'] else 'FULL'}] {t['external_id']}: {t['title']}")

    # TODO: Insert into database when DB connection is implemented (Step 2)
    print("\nSeed data validated. Database insertion will be implemented in Step 2.")


if __name__ == "__main__":
    main()

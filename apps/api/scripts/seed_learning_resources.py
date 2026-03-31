import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine

resources = [
    # Precision (P)
    ("Master Prompt Engineering Basics", "https://example.com/precision-basics", "P", 1, 3, "article"),
    ("Advanced Prompt Crafting", "https://example.com/precision-advanced", "P", 4, 6, "course"),
    ("Prompt Optimization Techniques", "https://example.com/precision-optimization", "P", 5, 7, "video"),

    # Efficiency (E)
    ("Token Optimization Guide", "https://example.com/efficiency-tokens", "E", 1, 4, "article"),
    ("Cost-Effective Prompting", "https://example.com/efficiency-cost", "E", 3, 6, "course"),
    ("Performance Tuning for LLMs", "https://example.com/efficiency-performance", "E", 5, 7, "tool"),

    # Clarity (C)
    ("Writing Clear Instructions", "https://example.com/clarity-instructions", "C", 1, 3, "article"),
    ("Structured Prompt Design", "https://example.com/clarity-structure", "C", 3, 5, "video"),
    ("Communication Best Practices", "https://example.com/clarity-communication", "C", 4, 7, "course"),

    # Adaptability (A)
    ("Multi-Model Prompting", "https://example.com/adaptability-multi", "A", 2, 5, "article"),
    ("Context-Aware Prompts", "https://example.com/adaptability-context", "A", 4, 6, "course"),
    ("Dynamic Prompt Strategies", "https://example.com/adaptability-dynamic", "A", 5, 7, "video"),

    # Mastery (M)
    ("Advanced Prompt Patterns", "https://example.com/mastery-patterns", "M", 5, 7, "course"),
    ("Expert Prompt Engineering", "https://example.com/mastery-expert", "M", 6, 7, "article"),
    ("Prompt Engineering at Scale", "https://example.com/mastery-scale", "M", 6, 7, "tool"),
]

async def seed():
    async with engine.begin() as conn:
        for title, url, pillar, min_level, max_level, resource_type in resources:
            await conn.execute(
                text("""
                    INSERT INTO learning_resources (title, url, pillar, min_level, max_level, resource_type)
                    VALUES (:title, :url, :pillar, :min_level, :max_level, :resource_type)
                """),
                {"title": title, "url": url, "pillar": pillar, "min_level": min_level,
                 "max_level": max_level, "resource_type": resource_type}
            )
    print(f"Seeded {len(resources)} learning resources")

if __name__ == "__main__":
    asyncio.run(seed())

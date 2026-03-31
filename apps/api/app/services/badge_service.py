"""Badge service: SVG generation with level, score, PECAM radar, date, mode label."""

import math
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.assessment import Assessment
from app.models.badge import Badge
from app.models.user import User

PILLARS = ["P", "E", "C", "A", "M"]
PILLAR_LABELS = {"P": "Precision", "E": "Efficiency", "C": "Creativity", "A": "Adaptability", "M": "Mastery"}

LEVEL_NAMES: dict[int, str] = {
    1: "Novice",
    2: "Practitioner",
    3: "Proficient",
    4: "Expert",
    5: "Master",
}

LEVEL_COLORS: dict[int, str] = {
    1: "#666666",
    2: "#008f11",
    3: "#00ff41",
    4: "#6D5FFA",
    5: "#EC41FB",
}


def _generate_radar_svg(pillar_scores: dict[str, Any], cx: float, cy: float, max_radius: float) -> str:
    """Generate SVG elements for a PECAM radar chart."""
    angle_step = 2 * math.pi / len(PILLARS)
    start_angle = -math.pi / 2

    def get_point(index: int, value: float) -> tuple[float, float]:
        angle = start_angle + index * angle_step
        r = (value / 100) * max_radius
        return (cx + r * math.cos(angle), cy + r * math.sin(angle))

    parts: list[str] = []

    for level_pct in [20, 40, 60, 80, 100]:
        points = " ".join(f"{get_point(i, level_pct)[0]:.1f},{get_point(i, level_pct)[1]:.1f}" for i in range(5))
        parts.append(f'<polygon points="{points}" fill="none" stroke="rgba(0,255,65,0.14)" stroke-width="0.7"/>')

    for i in range(5):
        x, y = get_point(i, 100)
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="rgba(0,255,65,0.14)" stroke-width="0.7"/>')

    data_points: list[tuple[float, float]] = []
    for i, p in enumerate(PILLARS):
        score_data = pillar_scores.get(p, {})
        score = float(score_data.get("combined", 0)) if isinstance(score_data, dict) else float(score_data)
        data_points.append(get_point(i, score))

    data_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in data_points)
    parts.append('<filter id="glow"><feGaussianBlur stdDeviation="2.5" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    parts.append(f'<polygon points="{data_str}" fill="rgba(0,255,65,0.2)" stroke="#00ff41" stroke-width="1.8" filter="url(#glow)"/>')

    for x, y in data_points:
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#00ff41"/>')

    label_radius = max_radius + 17
    for i, p in enumerate(PILLARS):
        angle = start_angle + i * angle_step
        lx = cx + label_radius * math.cos(angle)
        ly = cy + label_radius * math.sin(angle)
        score_data = pillar_scores.get(p, {})
        score = round(float(score_data.get("combined", 0))) if isinstance(score_data, dict) else round(float(score_data))
        parts.append(
            f'<text x="{lx:.1f}" y="{ly - 6:.1f}" text-anchor="middle" fill="#00ff41" '
            f'font-size="10" font-family="monospace" font-weight="bold">{p}</text>'
        )
        parts.append(
            f'<text x="{lx:.1f}" y="{ly + 8:.1f}" text-anchor="middle" fill="#66bf75" '
            f'font-size="7" font-family="monospace">{score}</text>'
        )

    return "\n    ".join(parts)


def _get_badge_domain() -> str:
    """Get the domain for badge verification URLs and branding."""
    return settings.deployment_domain or "promptranks.org"


def generate_badge_svg(
    level: int,
    level_name: str,
    final_score: float,
    pillar_scores: dict[str, Any],
    issued_at: datetime,
    mode: str,
    badge_id: str,
) -> str:
    """Generate a complete badge SVG with level, score, radar chart, date, and mode label."""
    color = LEVEL_COLORS.get(level, "#00ff41")
    mode_label = "Certified" if mode == "full" else "Estimated"
    date_str = issued_at.strftime("%Y-%m-%d")
    domain = _get_badge_domain()
    verification_url = f"https://{domain}/badges/verify/{badge_id}"
    domain_label = domain
    score_label = round(final_score)
    radar = _generate_radar_svg(pillar_scores, 270, 172, 54)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 320" width="520" height="320">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#07140a"/>
      <stop offset="55%" stop-color="#03070d"/>
      <stop offset="100%" stop-color="#000000"/>
    </linearGradient>
    <linearGradient id="panel" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="rgba(255,255,255,0.08)"/>
      <stop offset="100%" stop-color="rgba(255,255,255,0.02)"/>
    </linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{color}"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0.35"/>
    </linearGradient>
  </defs>

  <rect width="520" height="320" rx="24" fill="url(#bg)" stroke="{color}" stroke-width="2"/>
  <rect x="18" y="18" width="484" height="284" rx="20" fill="none" stroke="rgba(255,255,255,0.07)"/>

  <text x="34" y="40" fill="#00ff41" font-size="12" font-family="monospace" font-weight="bold" letter-spacing="3">PROMPTRANKS</text>
  <text x="34" y="58" fill="#6db776" font-size="8" font-family="monospace">VERIFIABLE AI PROMPT SKILL BADGE</text>

  <rect x="34" y="84" width="160" height="162" rx="18" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.08)"/>
  <rect x="52" y="102" width="124" height="124" rx="26" fill="url(#panel)" stroke="url(#accent)" stroke-width="1.4"/>
  <circle cx="114" cy="150" r="36" fill="rgba(0,0,0,0.3)" stroke="{color}" stroke-width="1.2"/>
  <circle cx="100" cy="142" r="4" fill="{color}"/>
  <circle cx="128" cy="142" r="4" fill="{color}"/>
  <path d="M97 166 Q114 178 131 166" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round"/>
  <text x="114" y="264" text-anchor="middle" fill="#a1d7a8" font-size="8" font-family="monospace">AVATAR SLOT</text>
  <text x="114" y="278" text-anchor="middle" fill="rgba(255,255,255,0.35)" font-size="7" font-family="monospace">deterministic placeholder</text>

  <rect x="214" y="84" width="272" height="40" rx="12" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.08)"/>
  <text x="232" y="101" fill="#6db776" font-size="8" font-family="monospace">LEVEL</text>
  <text x="232" y="116" fill="{color}" font-size="18" font-family="monospace" font-weight="bold">L{level} · {level_name}</text>

  <rect x="214" y="134" width="124" height="54" rx="14" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.08)"/>
  <text x="232" y="152" fill="#6db776" font-size="8" font-family="monospace">FINAL SCORE</text>
  <text x="232" y="178" fill="{color}" font-size="28" font-family="monospace" font-weight="bold">{score_label}</text>

  <rect x="350" y="134" width="136" height="54" rx="14" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.08)"/>
  <text x="368" y="152" fill="#6db776" font-size="8" font-family="monospace">MODE</text>
  <text x="368" y="178" fill="#f7f7ff" font-size="16" font-family="monospace" font-weight="bold">{mode_label}</text>

  <rect x="214" y="198" width="272" height="82" rx="18" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.08)"/>
  <g>
    {radar}
  </g>

  <line x1="34" y1="288" x2="486" y2="288" stroke="rgba(255,255,255,0.08)"/>
  <text x="34" y="304" fill="#6db776" font-size="8" font-family="monospace">Issued {date_str}</text>
  <text x="486" y="304" text-anchor="end" fill="rgba(255,255,255,0.42)" font-size="7" font-family="monospace">{domain_label}</text>
  <text x="260" y="304" text-anchor="middle" fill="rgba(255,255,255,0.46)" font-size="7" font-family="monospace">Verify {verification_url}</text>
</svg>'''

    return svg


async def create_badge(
    db: AsyncSession,
    user: User,
    assessment: Assessment,
) -> Badge:
    """Create a badge for a claimed assessment."""
    level = assessment.level or 1
    level_name = LEVEL_NAMES.get(level, "Novice")
    final_score = assessment.final_score or 0.0
    pillar_scores: dict[str, Any] = assessment.pillar_scores or {}
    mode = assessment.mode.value if hasattr(assessment.mode, "value") else str(assessment.mode)
    now = datetime.now(timezone.utc)

    badge_id = uuid.uuid4()
    badge_id_str = str(badge_id)

    badge_svg = generate_badge_svg(
        level=level,
        level_name=level_name,
        final_score=final_score,
        pillar_scores=pillar_scores,
        issued_at=now,
        mode=mode,
        badge_id=badge_id_str,
    )

    domain = _get_badge_domain()
    verification_url = f"https://{domain}/badges/verify/{badge_id_str}"

    badge = Badge(
        id=badge_id,
        user_id=user.id,
        assessment_id=assessment.id,
        mode=mode,
        level=level,
        level_name=level_name,
        final_score=final_score,
        pillar_scores=pillar_scores,
        badge_svg=badge_svg,
        verification_url=verification_url,
        issuer_domain=domain,
        issued_at=now,
    )
    db.add(badge)
    await db.commit()
    await db.refresh(badge)
    return badge

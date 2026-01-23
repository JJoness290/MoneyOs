import logging
import random
import re
from dataclasses import dataclass

from app.config import MIN_AUDIO_SECONDS

WORDS_PER_SECOND = 2.2
MAX_WORDS_PER_LINE = 12
MAX_LINES = 120


@dataclass
class ScriptResult:
    text: str
    estimated_seconds: float


def _estimate_seconds(text: str) -> float:
    word_count = len(text.split())
    return word_count / WORDS_PER_SECOND


def _trim_line(line: str) -> str:
    words = line.split()
    if len(words) <= MAX_WORDS_PER_LINE:
        return line
    return " ".join(words[:MAX_WORDS_PER_LINE])


def sanitize_script(text: str) -> str:
    cleaned = re.sub(r"[#/\\\\*_{}\\[\\]|><]", " ", text)
    cleaned = re.sub(r"`{1,3}.*?`{1,3}", " ", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"\\s+", " ", cleaned)
    return cleaned.strip()


def _story_theme() -> str:
    themes = [
        "relationship red flags",
        "friend betrayal",
        "work and boss situations",
        "family conflict",
        "realisation moments",
    ]
    return random.choice(themes)


def _build_story_lines() -> list[str]:
    theme = _story_theme()
    hooks = [
        "I didn't think this was a red flag at the time.",
        "I ignored a small sign, and it snowballed fast.",
        "I told myself it was nothing. It wasn't.",
        "I wish I noticed this sooner.",
    ]
    contexts = [
        f"This happened during a {theme} phase in my life.",
        "We were close, so I let things slide.",
        "It started as a normal week, nothing dramatic.",
        "I was trying to keep things calm and normal.",
    ]
    escalations = [
        "Little things kept piling up.",
        "The tone shifted in small ways I brushed off.",
        "I kept second-guessing my own reactions.",
        "I started feeling tense even before we spoke.",
    ]
    turning_points = [
        "Then one moment flipped everything.",
        "The turning point was quick and sharp.",
        "One comment finally made it click.",
        "A small scene made the whole pattern obvious.",
    ]
    reflections = [
        "After that, I saw how often I ignored my gut.",
        "I realized I was making excuses for behavior that hurt.",
        "Looking back, I wasn't being honest with myself.",
        "I learned that quiet discomfort adds up fast.",
    ]
    ctas = [
        "Has anyone else experienced this?",
        "Would you have noticed this sooner?",
        "Is this a common pattern, or just me?",
        "What would you have done differently?",
    ]

    base_lines = [
        random.choice(hooks),
        random.choice(contexts),
        random.choice(escalations),
        random.choice(turning_points),
        random.choice(reflections),
        random.choice(ctas),
    ]

    return [_trim_line(line) for line in base_lines]


def _truncate_lines(lines: list[str]) -> list[str]:
    if len(lines) <= MAX_LINES:
        return lines
    truncated = lines[:MAX_LINES]
    while truncated and not truncated[-1].rstrip().endswith((".", "!", "?")):
        truncated.pop()
    return truncated or lines[:MAX_LINES]

def generate_script(min_seconds: int = MIN_AUDIO_SECONDS) -> ScriptResult:
    lines: list[str] = []
    used = set()

    def add_unique(line: str) -> None:
        if line not in used:
            lines.append(line)
            used.add(line)

    try:
        for line in _build_story_lines():
            add_unique(line)

        lines = _truncate_lines(lines)
        script = "\\n".join(lines)
        estimated_seconds = _estimate_seconds(script)
        return ScriptResult(text=script, estimated_seconds=estimated_seconds)
    except Exception:  # noqa: BLE001
        logging.warning("Script generation encountered an error; returning partial script.")
        lines = _truncate_lines(lines)
        script = "\\n".join(lines)
        estimated_seconds = _estimate_seconds(script) if script else 0.0
        return ScriptResult(text=script, estimated_seconds=estimated_seconds)

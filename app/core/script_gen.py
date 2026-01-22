import logging
import random
from dataclasses import dataclass

from app.config import MIN_AUDIO_SECONDS

WORDS_PER_SECOND = 2.2
MAX_WORDS_PER_LINE = 12
MAX_LINES = 120
MAX_EXPANSION_PASSES = 2


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


def _expand_story_lines() -> list[str]:
    expansions = [
        "I kept telling myself I was overreacting.",
        "There were small pauses that felt heavy.",
        "I felt uneasy, but I stayed quiet.",
        "It got subtle, then it got loud.",
        "I noticed how I was walking on eggshells.",
        "I started replaying conversations in my head.",
        "I felt anxious for no clear reason.",
        "One day I realized I was always apologizing.",
        "The pattern was obvious once I named it.",
        "After that, I finally exhaled.",
    ]
    random.shuffle(expansions)
    return [_trim_line(line) for line in expansions]

def _truncate_lines(lines: list[str]) -> list[str]:
    if len(lines) <= MAX_LINES:
        return lines
    truncated = lines[:MAX_LINES]
    while truncated and not truncated[-1].rstrip().endswith((".", "!", "?")):
        truncated.pop()
    return truncated or lines[:MAX_LINES]

def _pad_recap(lines: list[str], max_lines: int) -> list[str]:
    recap_lines = [
        "I learned to trust the tension I felt.",
        "Now I pay attention to the first uneasy moment.",
        "It was a hard lesson, but it helped me reset.",
        "I still think about how fast it shifted.",
        "I try to listen to my own instincts now.",
        "It changed how I handle similar situations.",
    ]
    for line in recap_lines:
        if len(lines) >= max_lines:
            break
        if line not in lines:
            lines.append(_trim_line(line))
    return lines


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

        passes = 0
        while _estimate_seconds("\\n".join(lines)) < min_seconds and passes < MAX_EXPANSION_PASSES:
            for line in _expand_story_lines():
                if _estimate_seconds("\\n".join(lines)) >= min_seconds:
                    break
                add_unique(line)
            passes += 1

        if _estimate_seconds("\\n".join(lines)) < min_seconds:
            lines = _pad_recap(lines, MAX_LINES)

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

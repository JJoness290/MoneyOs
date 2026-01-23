import logging
import random
import re
from dataclasses import dataclass

from app.config import MIN_AUDIO_SECONDS

WORDS_PER_SECOND = 3.0
MAX_WORDS_PER_LINE = 12
MAX_LINES = 120
MIN_TARGET_SECONDS = 80
MAX_EXPANSION_PASSES = 4
EXPANSION_MIN_WORDS = 200
EXPANSION_MAX_WORDS = 250


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
    cleaned = re.sub(r"[#/\*_{}\[\]|><]", " ", text)
    cleaned = re.sub(r"`{1,3}.*?`{1,3}", " ", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"\s+", " ", cleaned)
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


def _expansion_sentences() -> list[str]:
    return [
        "Looking back, I see how small signals were adding weight each day.",
        "I kept trying to explain things away instead of naming what hurt.",
        "The hardest part was admitting I felt off long before the turning point.",
        "If you are unsure, notice the moments you feel relief when they are gone.",
        "I learned that comfort should not require constant self editing.",
        "I wish I had asked why I was always bracing before conversations.",
        "The pattern felt normal only because I kept shrinking to fit it.",
        "It helped me to write down the moments that felt heavy and repetitive.",
        "When I finally said it out loud, the situation made more sense.",
        "I realized that real care does not leave you confused for days.",
        "If you feel tense all the time, that is information you should trust.",
        "I started paying attention to how my body reacted before my words did.",
        "What I needed most was clarity, not another excuse to stay quiet.",
        "This taught me that kindness is not the same as endurance.",
        "I wish I had protected my peace earlier instead of later.",
        "You are allowed to step back when something keeps feeling wrong.",
        "It helped to hear other people share similar stories and name the feeling.",
        "Now I check in with myself instead of dismissing the discomfort.",
        "I try to choose environments where I do not have to perform calm.",
        "That change made my relationships feel lighter and more honest.",
    ]


def _build_expansion_block(used_sentences: set[str]) -> list[str]:
    sentences = [s for s in _expansion_sentences() if s not in used_sentences]
    block: list[str] = []
    word_count = 0
    for sentence in sentences:
        words = sentence.split()
        if word_count + len(words) > EXPANSION_MAX_WORDS:
            continue
        block.append(sentence)
        word_count += len(words)
        if word_count >= EXPANSION_MIN_WORDS:
            break
    if word_count < EXPANSION_MIN_WORDS:
        raise RuntimeError("Unable to build expansion block without repetition.")
    return [_trim_line(line) for line in block]


def _append_expansion(lines: list[str], used: set[str]) -> list[str]:
    block = _build_expansion_block(used)
    for line in block:
        if line not in used:
            lines.append(line)
            used.add(line)
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

        script = "\n".join(lines)
        estimated_seconds = _estimate_seconds(script)
        passes = 0
        while estimated_seconds < MIN_TARGET_SECONDS and passes < MAX_EXPANSION_PASSES:
            lines = _append_expansion(lines, used)
            lines = _truncate_lines(lines)
            script = "\n".join(lines)
            estimated_seconds = _estimate_seconds(script)
            passes += 1

        if estimated_seconds < MIN_TARGET_SECONDS:
            raise RuntimeError("Script too short after maximum expansion passes.")

        lines = _truncate_lines(lines)
        script = "\n".join(lines)
        estimated_seconds = _estimate_seconds(script)
        return ScriptResult(text=script, estimated_seconds=estimated_seconds)
    except Exception:  # noqa: BLE001
        logging.warning("Script generation encountered an error; returning partial script.")
        lines = _truncate_lines(lines)
        script = "\n".join(lines)
        estimated_seconds = _estimate_seconds(script) if script else 0.0
        return ScriptResult(text=script, estimated_seconds=estimated_seconds)


def expand_script_once(script_text: str) -> ScriptResult:
    lines = [line.strip() for line in script_text.splitlines() if line.strip()]
    used = set(lines)
    lines = _append_expansion(lines, used)
    lines = _truncate_lines(lines)
    expanded_text = "\n".join(lines)
    estimated_seconds = _estimate_seconds(expanded_text)
    return ScriptResult(text=expanded_text, estimated_seconds=estimated_seconds)

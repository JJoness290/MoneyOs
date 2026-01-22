import logging
import random
from dataclasses import dataclass

from app.config import MIN_AUDIO_SECONDS

WORDS_PER_SECOND = 2.2
MAX_WORDS_PER_LINE = 12
MAX_LINES = 120
MAX_PASSES = 10


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


def _build_base_lines() -> list[str]:
    opens = [
        "Stop scrolling for ten seconds.",
        "Quick shock: money obeys friction, not effort.",
        "Here is the weird rule most people miss.",
        "This is the money pattern nobody talks about.",
    ]
    contrasts = [
        "Working harder feels right, but it is a trap.",
        "Saving more is not the move. Saving earlier is.",
        "Budgeting fails when it is a mood, not a system.",
        "Spending looks fast. Outcomes are slow.",
    ]
    reveals = [
        "The rule is simple: remove steps from saving.",
        "The real switch is default behavior.",
        "Friction decides the outcome every time.",
        "Your money moves where your attention sits.",
    ]
    value_hits = [
        "Automate the transfer on payday.",
        "Rename accounts so your brain obeys the labels.",
        "Add a 24-hour pause for every cart checkout.",
        "Track hesitation, not transactions.",
    ]
    twists = [
        "Boring habits beat loud goals.",
        "Quiet systems create loud results.",
        "The smallest pause kills the biggest impulse.",
        "The real flex is stability, not hype.",
    ]
    ctas = [
        "Test this for one week and watch what changes.",
        "Try it today and see which habit breaks first.",
        "Save this so you can build the system later.",
        "Send this to your future self.",
    ]

    lines = [
        random.choice(opens),
        random.choice(contrasts),
        random.choice(reveals),
        random.choice(value_hits),
        random.choice(twists),
        random.choice(ctas),
    ]
    return [_trim_line(line) for line in lines]


def _expand_lines() -> list[str]:
    expansions = [
        "Every tap is a vote for tomorrow.",
        "Make spending slower than temptation.",
        "Make saving faster than excuses.",
        "Your calendar leaks money.",
        "Your phone makes buying frictionless.",
        "Fix the default, not the motivation.",
        "Replace guilt with design.",
        "Small switches create big outcomes.",
        "The rich move money first, then live.",
        "Most budgets fail after day three.",
        "Systems win when energy fades.",
        "Feel rich by removing tiny leaks.",
        "Friction is your secret ally.",
        "Attention decides what grows.",
        "Make the rule visible, then repeat it.",
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
        "Make it automatic, not emotional.",
        "Slow the spend. Speed the save.",
        "Design beats motivation.",
        "Keep the rule visible daily.",
        "Small switches create big outcomes.",
        "Friction is your ally.",
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
        for line in _build_base_lines():
            add_unique(line)

        passes = 0
        while _estimate_seconds("\\n".join(lines)) < min_seconds and passes < MAX_PASSES:
            for line in _expand_lines():
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

import random
from dataclasses import dataclass

from app.config import MIN_AUDIO_SECONDS

WORDS_PER_SECOND = 2.6


@dataclass
class ScriptResult:
    text: str
    estimated_seconds: float


def _estimate_seconds(text: str) -> float:
    word_count = len(text.split())
    return word_count / WORDS_PER_SECOND


def _base_sections() -> list[str]:
    hooks = [
        "Here is a question that should bother you:",
        "Quick thought experiment:",
        "Imagine this scenario:",
        "This is a quiet money mystery:",
    ]
    angles = [
        "Why do tiny habits beat giant plans?",
        "What actually controls your spending?",
        "How does attention change your financial outcomes?",
        "What makes wealth look boring up close?",
    ]
    bodies = [
        "Most people blame willpower, but the real driver is friction. If saving is hard, you will dodge it. If spending is easy, you will default to it.",
        "Your brain treats every purchase as a tiny vote for the future you live in. The problem is those votes happen at high speed, while results show up slowly.",
        "The fastest way to feel richer is to make money feel slower. A short pause before checkout can cut impulse spending more than any budget spreadsheet.",
        "A lifestyle that looks expensive on camera can still be fragile. The difference is whether money works quietly in the background or screams for attention.",
    ]
    tactics = [
        "One simple rule: decide on a default. Automate savings the day income lands, then let spending happen with what remains.",
        "Another rule: rename accounts by purpose. Your brain follows labels more than logic.",
        "Try a 24-hour buffer for online buys. If the desire survives a full day, it is real. If it vanishes, you just saved money.",
        "Track only one number for a week: how many times you hesitated. That hesitation count will tell you where your money leaks live.",
    ]
    closes = [
        "The point is not perfection. It is building a system that makes the right choice the easy choice.",
        "If you want your money to grow, give it a stable rhythm instead of dramatic resets.",
        "Small design choices beat big motivation speeches. You can feel the difference in a month.",
        "The secret is boring on purpose. Boring is what compounds.",
    ]
    return [
        f"{random.choice(hooks)} {random.choice(angles)}",
        random.choice(bodies),
        random.choice(tactics),
        random.choice(closes),
    ]


def generate_script(min_seconds: int = MIN_AUDIO_SECONDS) -> ScriptResult:
    sections = []
    while True:
        sections.extend(_base_sections())
        script = " ".join(sections)
        estimated_seconds = _estimate_seconds(script)
        if estimated_seconds >= min_seconds:
            return ScriptResult(text=script, estimated_seconds=estimated_seconds)

        sections.append(
            "Here is the twist: the small changes feel tiny today, but they stack into real freedom when you stop leaking attention."
        )

import logging
import random
import re
from dataclasses import dataclass

from app.config import MIN_AUDIO_SECONDS

WORDS_PER_SECOND = 3.0
MAX_WORDS_PER_LINE = 12
MAX_LINES = 400
MIN_TARGET_SECONDS = 80
MIN_TARGET_WORDS = 2200
MAX_TARGET_WORDS = 3000
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
        "incentive design in digital platforms",
        "how metrics reshape human judgment",
        "why status systems distort decisions",
        "the psychology of compliance in modern workplaces",
        "the invisible economics of attention",
    ]
    return random.choice(themes)


def _truncate_lines(lines: list[str]) -> list[str]:
    if len(lines) <= MAX_LINES:
        return lines
    truncated = lines[:MAX_LINES]
    while truncated and not truncated[-1].rstrip().endswith((".", "!", "?")):
        truncated.pop()
    return truncated or lines[:MAX_LINES]


def _section_templates() -> dict[str, list[str]]:
    return {
        "cold_open": [
            "Most systems reward what they can measure, not what they truly need.",
            "The strange part is that the numbers feel objective, but they are steering us.",
            "Here is the contradiction: better data can make worse decisions.",
            "The question is not who is right, but which incentives are doing the talking.",
            "If you want to understand modern power, follow the metrics people optimize.",
        ],
        "problem_setup": [
            "We live inside systems that translate messy human goals into simplified scores.",
            "Those scores do not just reflect reality, they reshape it by defining success.",
            "People adapt quickly to whatever is rewarded, even when it conflicts with intention.",
            "This matters because money, status, and opportunity flow through these scoreboards.",
            "The result is a quiet drift from values to outputs, from meaning to measurement.",
        ],
        "system_explanation": [
            "Incentives work by narrowing attention to what gets counted and repeated.",
            "Once a metric exists, people learn how to improve it, whether or not it helps.",
            "Technology accelerates this feedback loop by making measurement constant.",
            "Systems prefer signals that are easy to aggregate, even if they are shallow.",
            "Psychology adds fuel: humans chase visible progress, especially under pressure.",
            "When careers and budgets depend on a metric, it becomes the real goal.",
            "This is how local optimization can quietly undermine the original mission.",
            "The architecture looks rational, but it rewards strategic behavior over truth.",
            "The more complex the system, the more people rely on proxies to decide.",
        ],
        "hidden_consequences": [
            "Second order effects emerge when everyone learns the same shortcuts.",
            "Those who can game the metric gain influence, even if they create fragility.",
            "Groups with less access to the rules are forced to compete on worse terms.",
            "Over time, the system selects for conformity to the metric instead of competence.",
            "This can hollow out trust because outcomes feel disconnected from reality.",
        ],
        "big_picture": [
            "Zooming out, incentives become a language that links psychology, money, and power.",
            "Technology scales that language, making it harder to see the tradeoffs.",
            "Society then reorganizes around what is legible to the system, not what is wise.",
            "The deeper insight is that measurement is a political act, not a neutral one.",
        ],
        "closing": [
            "A useful question is not how to win the game, but who wrote the rules.",
            "If you change the incentive, you change the story the system tells itself.",
            "That is why the most powerful shifts happen quietly, inside the metrics.",
        ],
    }


def _phrase_pools() -> dict[str, list[str]]:
    return {
        "agents": [
            "managers",
            "platform designers",
            "policy teams",
            "investors",
            "operators",
            "engineers",
            "frontline workers",
            "regulators",
        ],
        "systems": [
            "platforms",
            "markets",
            "institutions",
            "organizations",
            "algorithms",
            "workflows",
            "rating systems",
        ],
        "metrics": [
            "engagement",
            "productivity",
            "compliance",
            "growth",
            "risk",
            "output",
            "efficiency",
        ],
        "effects": [
            "distort judgment",
            "change behavior",
            "compress nuance",
            "reward shortcuts",
            "shift incentives",
            "redefine success",
            "hide tradeoffs",
        ],
        "stakes": [
            "capital allocation",
            "status hierarchies",
            "career mobility",
            "public trust",
            "social legitimacy",
            "strategic advantage",
        ],
    }


def _generate_sentences(section: str, target_words: int, used: set[str]) -> list[str]:
    pools = _phrase_pools()
    templates = [
        "{agent} inside {system} optimize for {metric} because it is visible and rewarded.",
        "When {metric} becomes the scoreboard, it can {effect} across the whole system.",
        "The system feels objective, yet it can {effect} in ways people rarely notice.",
        "{agent} often chase {metric} to protect {stake}, even when it backfires later.",
        "In complex {system}, proxies for {metric} become the fastest path to decisions.",
        "What looks like progress can {effect} the feedback people depend on.",
        "The system rewards alignment with {metric}, not alignment with the original mission.",
        "This is why {system} can {effect} when incentives tighten under pressure.",
    ]
    seed_sentences = _section_templates().get(section, [])
    sentences = []
    word_count = 0
    for sentence in seed_sentences:
        if sentence not in used:
            sentences.append(sentence)
            used.add(sentence)
            word_count += len(sentence.split())
    attempts = 0
    while word_count < target_words and attempts < 2000:
        template = random.choice(templates)
        sentence = template.format(
            agent=random.choice(pools["agents"]),
            system=random.choice(pools["systems"]),
            metric=random.choice(pools["metrics"]),
            effect=random.choice(pools["effects"]),
            stake=random.choice(pools["stakes"]),
        )
        attempts += 1
        if sentence in used:
            continue
        used.add(sentence)
        sentences.append(sentence)
        word_count += len(sentence.split())
    if word_count < target_words:
        raise RuntimeError("Unable to generate enough unique sentences for section.")
    return [_trim_line(line) for line in sentences]


def _build_expansion_block(used_sentences: set[str]) -> list[str]:
    sentences = _generate_sentences("system_explanation", EXPANSION_MIN_WORDS, used_sentences)
    words = 0
    block: list[str] = []
    for sentence in sentences:
        sentence_words = len(sentence.split())
        if words + sentence_words > EXPANSION_MAX_WORDS:
            continue
        block.append(sentence)
        words += sentence_words
        if words >= EXPANSION_MIN_WORDS:
            break
    if words < EXPANSION_MIN_WORDS:
        raise RuntimeError("Unable to build expansion block without repetition.")
    return block


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

    for line in _generate_sentences("cold_open", 140, used):
        add_unique(line)
    lines.append("")
    for line in _generate_sentences("problem_setup", 320, used):
        add_unique(line)
    lines.append("")
    for line in _generate_sentences("system_explanation", 650, used):
        add_unique(line)
    lines.append("")
    for line in _generate_sentences("hidden_consequences", 300, used):
        add_unique(line)
    lines.append("")
    for line in _generate_sentences("big_picture", 240, used):
        add_unique(line)
    lines.append("")
    for line in _generate_sentences("closing", 120, used):
        add_unique(line)

    lines = [line for line in lines if line.strip()]
    script = "\n".join(lines)
    estimated_seconds = _estimate_seconds(script)
    word_count = len(script.split())
    passes = 0
    while (estimated_seconds < MIN_TARGET_SECONDS or word_count < MIN_TARGET_WORDS) and passes < MAX_EXPANSION_PASSES:
        lines = _append_expansion(lines, used)
        lines = _truncate_lines(lines)
        script = "\n".join(lines)
        estimated_seconds = _estimate_seconds(script)
        word_count = len(script.split())
        passes += 1

    if estimated_seconds < MIN_TARGET_SECONDS or word_count < MIN_TARGET_WORDS:
        raise RuntimeError("Script too short after maximum expansion passes.")
    if word_count > MAX_TARGET_WORDS:
        raise RuntimeError("Script exceeds maximum target word count.")

    lines = _truncate_lines(lines)
    script = "\n".join(lines)
    estimated_seconds = _estimate_seconds(script)
    return ScriptResult(text=script, estimated_seconds=estimated_seconds)


def expand_script_once(script_text: str) -> ScriptResult:
    lines = [line.strip() for line in script_text.splitlines() if line.strip()]
    used = set(lines)
    lines = _append_expansion(lines, used)
    lines = _truncate_lines(lines)
    expanded_text = "\n".join(lines)
    estimated_seconds = _estimate_seconds(expanded_text)
    return ScriptResult(text=expanded_text, estimated_seconds=estimated_seconds)

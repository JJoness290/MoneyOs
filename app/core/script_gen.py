import random
import re
from dataclasses import dataclass

from app.config import MIN_AUDIO_SECONDS

WORDS_PER_SECOND = 3.0
MAX_WORDS_PER_LINE = 18
MAX_LINES = 520
MIN_TARGET_SECONDS = 600
MIN_TARGET_WORDS = 2000
MAX_TARGET_WORDS = 3000
MAX_EXPANSION_PASSES = 0


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


def _truncate_lines(lines: list[str]) -> list[str]:
    if len(lines) <= MAX_LINES:
        return lines
    truncated = lines[:MAX_LINES]
    while truncated and not truncated[-1].rstrip().endswith((".", "!", "?")):
        truncated.pop()
    return truncated or lines[:MAX_LINES]


def _expansion_axes() -> list[str]:
    return [
        "historical_evolution",
        "incentive_structures",
        "failure_modes",
        "alternative_systems",
        "psychological_biases",
        "second_order_effects",
        "third_order_effects",
        "long_term_consequences",
        "persistent_myths",
        "why_misunderstood",
    ]


def _topic_pool() -> list[dict]:
    return [
        {
            "topic": "how performance metrics reshape decisions inside modern institutions",
            "axes": [
                "historical_evolution",
                "incentive_structures",
                "failure_modes",
                "psychological_biases",
                "second_order_effects",
            ],
        },
        {
            "topic": "why algorithmic ranking systems reward the wrong behaviors",
            "axes": [
                "historical_evolution",
                "incentive_structures",
                "alternative_systems",
                "third_order_effects",
                "persistent_myths",
            ],
        },
        {
            "topic": "how financial incentives distort truth in knowledge platforms",
            "axes": [
                "historical_evolution",
                "incentive_structures",
                "failure_modes",
                "psychological_biases",
                "long_term_consequences",
            ],
        },
    ]


def _select_topic() -> dict:
    topics = _topic_pool()
    chosen = random.choice(topics)
    available_axes = [axis for axis in chosen["axes"] if axis in _expansion_axes()]
    if len(available_axes) < 4:
        raise RuntimeError("Not enough expansion axes available for planning.")
    chosen["axes"] = available_axes
    return chosen


def _section_templates(topic: str) -> dict[str, list[str]]:
    return {
        "cold_open": [
            f"Here is the strange part about {topic}.",
            "The numbers look clean, but the behavior gets messy.",
            "We measure the wrong thing and then blame people for the outcome.",
            "The real story is not who failed. It is what the system rewarded.",
            "Once you see the incentives, the pattern becomes obvious.",
        ],
        "problem_setup": [
            "Most people assume metrics reflect reality. They do not.",
            "They shape reality by deciding what counts as success.",
            "That matters because money, status, and jobs follow the scoreboard.",
            "People adapt fast when rewards are on the line.",
            "So the system starts changing people, not just measuring them.",
        ],
        "core_system": [
            "Incentives narrow attention. That is their job.",
            "Once a metric exists, people learn how to move it.",
            "Technology speeds up that feedback loop.",
            "Psychology adds pressure to chase visible progress.",
            "If a career depends on a number, that number becomes the goal.",
            "Local optimization feels rational, even when it breaks the mission.",
            "The system rewards alignment with the metric, not the truth.",
        ],
        "big_picture": [
            "Zoom out and you can see the structure at work.",
            "Psychology decides what people chase.",
            "Money decides what gets scaled.",
            "Technology decides what gets measured.",
            "Society then reorganizes around what is legible to the system.",
        ],
        "closing": [
            "The quiet power is in the incentives, not the slogans.",
            "Change the metric and you change the behavior.",
            "That is where real system change begins.",
        ],
    }


def _axis_templates(axis: str) -> list[str]:
    templates = {
        "historical_evolution": [
            "History is full of moments where scale forced new measurements.",
            "When trust breaks, metrics step in.",
            "Over time the metric becomes the language of authority.",
        ],
        "incentive_structures": [
            "Incentives decide who can win without changing the rules.",
            "Those closest to the metric learn how to shape it.",
            "Rewards travel toward what is easiest to count.",
        ],
        "failure_modes": [
            "One failure mode is Goodhart's Law.",
            "When a measure becomes a target, it stops being a measure.",
            "Another failure is signal inflation, where activity replaces outcomes.",
        ],
        "alternative_systems": [
            "Some systems slow decisions to protect judgment.",
            "Others mix qualitative and quantitative signals.",
            "Decentralized models can reduce single-metric dominance.",
        ],
        "psychological_biases": [
            "We overweight what is recent and visible.",
            "Status bias makes the scoreboard feel sacred.",
            "Loss aversion pushes people to defend a bad metric.",
        ],
        "second_order_effects": [
            "Second-order effects appear when people chase the metric, not the mission.",
            "The system then rewards those tactics as if they were success.",
            "That shifts behavior even further away from intent.",
        ],
        "third_order_effects": [
            "Third-order effects reshape culture.",
            "Compliance starts to look like competence.",
            "Learning slows because the signal gets too loud.",
        ],
        "long_term_consequences": [
            "Over time, incentives change which skills get rewarded.",
            "Capital flows toward the most legible signals.",
            "The long-term cost is slower adaptation.",
        ],
        "persistent_myths": [
            "A common myth is that more data always improves decisions.",
            "Another myth is that metrics remove bias.",
            "Optimization often just hides tradeoffs.",
        ],
        "why_misunderstood": [
            "Smart people still miss this because the feedback is delayed.",
            "The benefits are concentrated and the harms are diffuse.",
            "So the system feels stable even when it drifts.",
        ],
    }
    return templates.get(axis, [])


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


def _sentence_similarity(candidate: str, existing: str) -> float:
    candidate_tokens = set(candidate.lower().split())
    existing_tokens = set(existing.lower().split())
    if not candidate_tokens or not existing_tokens:
        return 0.0
    overlap = candidate_tokens.intersection(existing_tokens)
    return len(overlap) / max(len(candidate_tokens), len(existing_tokens))


def _is_repetitive(candidate: str, used: set[str]) -> bool:
    for sentence in used:
        if _sentence_similarity(candidate, sentence) >= 0.7:
            return True
    return False


def _generate_sentences(section: str, target_words: int, used: set[str], axis: str | None = None, topic: str | None = None) -> list[str]:
    pools = _phrase_pools()
    templates = [
        "{agent} inside {system} chase {metric} because it is the visible score.",
        "When {metric} becomes the scoreboard, the system can {effect}.",
        "The system feels objective, yet it can {effect} in quiet ways.",
        "{agent} protect {stake} by pushing {metric}, even when it backfires.",
        "In complex {system}, proxies for {metric} guide fast decisions.",
        "What looks like progress can {effect} the signal people trust.",
        "The system rewards the metric, not the mission.",
        "When incentives tighten, {system} tend to {effect}.",
    ]
    seed_sentences = _section_templates(topic or "the system").get(section, [])
    if axis:
        seed_sentences = seed_sentences + _axis_templates(axis)
    sentences = []
    word_count = 0
    for sentence in seed_sentences:
        if sentence in used or _is_repetitive(sentence, used):
            raise RuntimeError("Repetition detected in seed sentences.")
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
        if sentence in used or _is_repetitive(sentence, used):
            continue
        used.add(sentence)
        sentences.append(sentence)
        word_count += len(sentence.split())
    if word_count < target_words:
        raise RuntimeError("Unable to generate enough unique sentences for section.")
    return [_trim_line(line) for line in sentences]


def _build_outline(axes: list[str]) -> list[tuple[str, str | None, int]]:
    return [
        ("cold_open", None, 160),
        ("problem_setup", None, 460),
        ("core_system", None, 1200),
        ("expansion_axis_a", axes[0], 260),
        ("expansion_axis_b", axes[1], 260),
        ("expansion_axis_c", axes[2], 260),
        ("big_picture", None, 460),
        ("closing", None, 160),
    ]


def _insert_breaks(sentences: list[str]) -> list[str]:
    output = []
    count = 0
    for sentence in sentences:
        output.append(sentence)
        count += 1
        if count >= random.randint(1, 3):
            output.append("")
            count = 0
    return output


def _validate_no_repetition(lines: list[str]) -> None:
    seen = []
    for sentence in lines:
        if not sentence.strip():
            continue
        for prior in seen:
            if _sentence_similarity(sentence, prior) >= 0.7:
                raise RuntimeError("Repetition detected in generated script.")
        seen.append(sentence)


def generate_script(min_seconds: int = MIN_AUDIO_SECONDS) -> ScriptResult:
    lines: list[str] = []
    used = set()

    topic_plan = _select_topic()
    axes = topic_plan["axes"]
    if len(axes) < 3:
        raise RuntimeError("Not enough expansion axes available for planning.")

    outline = _build_outline(axes)
    for section, axis, target_words in outline:
        sentences = _generate_sentences(section, target_words, used, axis, topic_plan["topic"])
        lines.extend(_insert_breaks(sentences))

    script = "\n".join(lines).strip()
    estimated_seconds = _estimate_seconds(script)
    word_count = len(script.split())

    if estimated_seconds < MIN_TARGET_SECONDS:
        raise RuntimeError("Script too short after initial planning.")
    if word_count < MIN_TARGET_WORDS:
        raise RuntimeError("Script word count below minimum target.")
    if word_count > MAX_TARGET_WORDS:
        raise RuntimeError("Script exceeds maximum target word count.")

    lines = _truncate_lines(lines)
    script = "\n".join(lines).strip()
    estimated_seconds = _estimate_seconds(script)
    _validate_no_repetition(lines)
    return ScriptResult(text=script, estimated_seconds=estimated_seconds)


def expand_script_once(script_text: str) -> ScriptResult:
    raise RuntimeError("Script expansion after planning is disabled.")


def generate_titles(script_text: str) -> list[str]:
    titles = [
        "Why This System Rewards the Wrong People",
        "The Hidden Logic Behind Modern Work",
        "This Incentive Quietly Changed Everything",
        "How Metrics Became a Form of Power",
        "The Psychological Cost of Incentive Design",
        "What Technology Counts, Society Becomes",
    ]
    random.shuffle(titles)
    return titles[:3]


def generate_description(script_text: str) -> str:
    return (
        "A clear explanation of how incentives, technology, and psychology shape "
        "modern systems, why metrics become power, and what second-order effects "
        "emerge when organizations optimize for the wrong signals."
    )

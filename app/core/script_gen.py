import logging
import random
import re
from dataclasses import dataclass

from app.config import MIN_AUDIO_SECONDS

WORDS_PER_SECOND = 3.0
MAX_WORDS_PER_LINE = 12
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
            "topic": "How performance metrics reshape decisions inside modern institutions",
            "axes": [
                "historical_evolution",
                "incentive_structures",
                "failure_modes",
                "psychological_biases",
                "second_order_effects",
            ],
        },
        {
            "topic": "Why algorithmic ranking systems reward the wrong behaviors",
            "axes": [
                "historical_evolution",
                "incentive_structures",
                "alternative_systems",
                "third_order_effects",
                "persistent_myths",
            ],
        },
        {
            "topic": "How financial incentives distort truth in knowledge platforms",
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
        "core_system": [
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


def _axis_templates(axis: str) -> list[str]:
    templates = {
        "historical_evolution": [
            "Historically, measurement expanded whenever organizations scaled beyond personal trust.",
            "Early systems relied on judgment, but scale forced the creation of proxies.",
            "Once proxy metrics appeared, they became the default language of authority.",
        ],
        "incentive_structures": [
            "Incentive structures decide who can win without changing the rules.",
            "Those closest to the metric learn to shape it, while others bear the cost.",
            "Rewards travel toward what is easiest to count, not what is most valuable.",
        ],
        "failure_modes": [
            "A common failure mode is Goodhart's Law: when a measure becomes a target, it stops being a measure.",
            "Another failure mode is signaling inflation, where visible activity replaces meaningful outcomes.",
            "Systems also fail by overfitting to past data and missing new risks.",
        ],
        "alternative_systems": [
            "Alternative systems often rely on mixed signals, combining qualitative and quantitative inputs.",
            "Some models slow down decision cycles to protect against metric manipulation.",
            "Others decentralize authority to reduce the impact of any single metric.",
        ],
        "psychological_biases": [
            "Humans overweight what is recent and visible, which makes metrics feel more real than they are.",
            "Status bias pushes people to protect the scoreboard, even when it becomes inaccurate.",
            "Loss aversion encourages short-term metric defense over long-term system health.",
        ],
        "second_order_effects": [
            "Second-order effects appear when people change behavior to satisfy the metric, not the mission.",
            "Third-order effects appear when the system begins rewarding those changes as if they were success.",
            "Eventually the system optimizes for appearances rather than outcomes.",
        ],
        "third_order_effects": [
            "Third-order effects reshape culture, making compliance look like competence.",
            "Over time, the system rewards those who master the signals, not the substance.",
            "This creates a feedback loop that crowds out dissent and slows learning.",
        ],
        "long_term_consequences": [
            "Over time, these incentives reshape culture and determine which skills are valued.",
            "They also influence capital flows, reinforcing power structures that look efficient on paper.",
            "The long-term cost is a slower ability to adapt when the environment changes.",
        ],
        "persistent_myths": [
            "A common myth is that more data always improves decisions.",
            "Another myth is that metrics reduce bias, even though they often encode it.",
            "People also assume that optimization equals progress, which is not always true.",
        ],
        "why_misunderstood": [
            "Intelligent people still misunderstand the system because the feedback is delayed and indirect.",
            "The benefits are concentrated, while the harms are diffuse and harder to measure.",
            "That makes the system feel stable even when it is drifting off course.",
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


def _generate_sentences(section: str, target_words: int, used: set[str], axis: str | None = None) -> list[str]:
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
    if axis:
        seed_sentences = seed_sentences + _axis_templates(axis)
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


def _build_outline(topic: str, axes: list[str]) -> list[tuple[str, str | None, int]]:
    return [
        ("cold_open", None, 140),
        ("problem_setup", None, 420),
        ("core_system", None, 950),
        ("expansion_axis_a", axes[0], 260),
        ("expansion_axis_b", axes[1], 260),
        ("expansion_axis_c", axes[2], 260),
        ("big_picture", None, 420),
        ("closing", None, 150),
    ]


def generate_script(min_seconds: int = MIN_AUDIO_SECONDS) -> ScriptResult:
    lines: list[str] = []
    used = set()

    topic_plan = _select_topic()
    axes = topic_plan["axes"]
    if len(axes) < 3:
        raise RuntimeError("Not enough expansion axes available for planning.")

    outline = _build_outline(topic_plan["topic"], axes)
    for section, axis, target_words in outline:
        lines.extend(_generate_sentences(section, target_words, used, axis))
        lines.append("")

    lines = [line for line in lines if line.strip()]
    script = "\n".join(lines)
    estimated_seconds = _estimate_seconds(script)
    word_count = len(script.split())

    if estimated_seconds < MIN_TARGET_SECONDS:
        raise RuntimeError("Script too short after initial planning.")
    if word_count < MIN_TARGET_WORDS:
        raise RuntimeError("Script word count below minimum target.")
    if word_count > MAX_TARGET_WORDS:
        raise RuntimeError("Script exceeds maximum target word count.")

    lines = _truncate_lines(lines)
    script = "\n".join(lines)
    estimated_seconds = _estimate_seconds(script)
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

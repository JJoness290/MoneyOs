import random
import re
from collections import Counter

STOPWORDS = {
    "about",
    "after",
    "before",
    "being",
    "because",
    "between",
    "could",
    "should",
    "there",
    "their",
    "these",
    "those",
    "which",
    "your",
    "with",
    "that",
    "this",
    "what",
    "when",
    "where",
    "who",
    "will",
    "just",
    "into",
    "than",
    "then",
    "have",
    "from",
    "they",
    "them",
    "been",
    "does",
    "every",
    "easy",
    "make",
    "more",
    "most",
    "much",
    "very",
    "like",
}

IMPLIED_VISUALS = {
    "scrolling": ["phone scrolling", "thumb swipe", "social media feed"],
    "scroll": ["phone scrolling", "thumb swipe", "social media feed"],
    "money": ["cash closeup", "counting cash", "wallet hands"],
    "budget": ["budget notebook", "calculator hands", "spreadsheet desk"],
    "saving": ["saving jar", "piggy bank", "transfer app"],
    "spending": ["checkout counter", "card payment", "shopping cart"],
    "work": ["office work", "typing hands", "late night desk"],
    "attention": ["focused face", "concentration", "eyes closeup"],
    "system": ["workflow", "checklist", "automation app"],
    "habit": ["routine morning", "alarm clock", "daily planner"],
    "phone": ["phone screen", "mobile app", "hands phone"],
    "impulse": ["impulse buy", "checkout tap", "shopping decision"],
    "friction": ["slow motion hands", "pause gesture", "hesitation"],
    "default": ["settings screen", "toggle switch", "automation"],
    "leak": ["dripping water", "leaking pipe", "wasting time"],
    "calendar": ["calendar planning", "schedule board", "planner desk"],
    "rich": ["city skyline", "modern lifestyle", "success routine"],
    "boring": ["quiet office", "minimal desk", "calm workspace"],
    "future": ["sunrise city", "long road", "looking ahead"],
}

FALLBACK_QUERIES = [
    "city motion",
    "hands typing",
    "people walking street",
    "night office",
    "phone closeup",
    "abstract motion",
]


def split_script(script: str, max_lines_per_segment: int = 2) -> list[str]:
    lines = [line.strip() for line in script.splitlines() if line.strip()]
    if not lines:
        return [script]
    segments = []
    for i in range(0, len(lines), max_lines_per_segment):
        segments.append(" ".join(lines[i : i + max_lines_per_segment]))
    return segments


def _tokenize(text: str) -> list[str]:
    tokens = [
        "".join(char for char in word.lower() if char.isalpha())
        for word in re.split(r"\s+", text)
    ]
    return [token for token in tokens if token and token not in STOPWORDS]


def _top_keywords(tokens: list[str], limit: int = 4) -> list[str]:
    if not tokens:
        return []
    counts = Counter(tokens)
    return [word for word, _ in counts.most_common(limit)]


def extract_queries(text: str, min_queries: int = 3, max_queries: int = 5) -> list[str]:
    tokens = _tokenize(text)
    keywords = _top_keywords(tokens)
    implied = []
    for token in keywords:
        implied.extend(IMPLIED_VISUALS.get(token, []))

    queries = []
    for phrase in implied:
        queries.append(phrase)

    if keywords:
        queries.append(" ".join(keywords[:2]))
        if len(keywords) > 2:
            queries.append(" ".join(keywords[1:3]))

    while len(queries) < min_queries:
        queries.append(random.choice(FALLBACK_QUERIES))

    random.shuffle(queries)
    return queries[:max_queries]


def build_query_sets(script_segments: list[str]) -> list[list[str]]:
    return [extract_queries(segment) for segment in script_segments]

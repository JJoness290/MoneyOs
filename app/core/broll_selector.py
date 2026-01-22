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
}

DEFAULT_KEYWORDS = [
    "city",
    "technology",
    "lifestyle",
    "people",
    "abstract",
    "motion",
]


def split_script(script: str, segments: int = 6) -> list[str]:
    words = script.split()
    if segments <= 1:
        return [script]
    chunk_size = max(1, len(words) // segments)
    parts = []
    for index in range(0, len(words), chunk_size):
        parts.append(" ".join(words[index : index + chunk_size]))
    if len(parts) > segments:
        parts = parts[:segments - 1] + [" ".join(parts[segments - 1 :])]
    return parts


def extract_keywords(text: str, max_keywords: int = 3) -> list[str]:
    tokens = [
        "".join(char for char in word.lower() if char.isalpha())
        for word in text.split()
    ]
    filtered = [token for token in tokens if len(token) > 4 and token not in STOPWORDS]
    if not filtered:
        return DEFAULT_KEYWORDS[:max_keywords]
    counts = Counter(filtered)
    keywords = [word for word, _ in counts.most_common(max_keywords)]
    return keywords


def build_keyword_sets(script_segments: list[str]) -> list[list[str]]:
    return [extract_keywords(segment) for segment in script_segments]

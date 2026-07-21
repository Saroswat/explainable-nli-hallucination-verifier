import json
import re
from pathlib import Path

from verinli.retrieval import Passage

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


def passages_from_text(
    text: str,
    source: str = "plain-text",
    max_characters: int = 800,
) -> list[Passage]:
    """Split ordinary text into deterministic, source-labelled evidence passages."""
    if max_characters < 100:
        raise ValueError("max_characters must be at least 100.")
    paragraphs = [item.strip() for item in re.split(r"\n\s*\n", text) if item.strip()]
    chunks: list[str] = []
    for paragraph in paragraphs:
        sentences = [item.strip() for item in _SENTENCE_BOUNDARY.split(paragraph) if item.strip()]
        current = ""
        for sentence in sentences:
            if current and len(current) + len(sentence) + 1 > max_characters:
                chunks.append(current)
                current = sentence
            else:
                current = f"{current} {sentence}".strip()
        if current:
            chunks.append(current)

    return [
        Passage(passage_id=f"text-{index:03d}", text=chunk, source=source)
        for index, chunk in enumerate(chunks, start=1)
    ]


def passages_from_jsonl(text: str) -> list[Passage]:
    """Parse JSON Lines evidence with useful line-level validation errors."""
    passages: list[Passage] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
            passages.append(Passage(**value))
        except (json.JSONDecodeError, TypeError) as error:
            raise ValueError(f"Invalid JSONL evidence on line {line_number}: {error}") from error
    return passages


def load_evidence_file(path: Path) -> list[Passage]:
    """Load JSONL or plain-text/Markdown evidence from disk."""
    if not path.is_file():
        raise ValueError(f"Evidence file not found: {path}")
    content = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".jsonl":
        passages = passages_from_jsonl(content)
    else:
        passages = passages_from_text(content, source=path.name)
    if not passages:
        raise ValueError("The evidence file must contain at least one passage.")
    return passages

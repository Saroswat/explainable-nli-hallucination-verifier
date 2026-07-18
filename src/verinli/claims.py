import re

_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


def split_atomic_claims(answer: str) -> list[str]:
    """Conservative sentence/clause splitter with deterministic output."""
    claims: list[str] = []
    for sentence in _BOUNDARY.split(answer.strip()):
        sentence = sentence.strip(" \n\t.-")
        if not sentence:
            continue
        parts = re.split(r"\s*;\s*|\s+\b(?:but|whereas)\b\s+", sentence, flags=re.I)
        claims.extend(part.strip(" ,") for part in parts if len(part.strip().split()) >= 3)
    return claims

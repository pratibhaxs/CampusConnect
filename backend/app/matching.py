"""Name normalization + fuzzy matching, used to stop duplicate companies/roles.

Layer 1: normalize (lowercase, drop punctuation and legal suffixes, expand aliases).
Layer 2: rapidfuzz similarity on the normalized names (0-100).
No external API and no model — deterministic and easy to explain.
"""
import re
from typing import Iterable, Optional

from rapidfuzz import fuzz

# Words that carry no identity ("Infosys Ltd" == "Infosys").
_SUFFIXES = {
    "pvt", "private", "ltd", "limited", "inc", "incorporated", "llc", "llp",
    "corp", "corporation", "co", "company", "technologies", "technology",
}

# Abbreviation -> full name. Looked up on the normalized text, so add lowercase keys.
ALIASES = {
    "tcs": "tata consultancy services",
    "hcl": "hcl technologies",
    "l and t": "larsen and toubro",
    "lt": "larsen and toubro",
    "ibm india": "ibm",
    "cts": "cognizant",
    "ms": "microsoft",
}

DEFAULT_THRESHOLD = 85  # "probably the same entity" — ask the user to confirm
FLAG_THRESHOLD = 70     # "looks related" — remember it so an admin can review


def normalize_name(name: str) -> str:
    text = (name or "").lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = ALIASES.get(text, text)
    words = [w for w in text.split() if w not in _SUFFIXES]
    return " ".join(words) if words else text


def similarity(a_normalized: str, b_normalized: str) -> int:
    """Best of plain and word-order-insensitive ratio, as an int 0-100."""
    if not a_normalized or not b_normalized:
        return 0
    return int(round(max(
        fuzz.ratio(a_normalized, b_normalized),
        fuzz.token_sort_ratio(a_normalized, b_normalized),
    )))


def find_matches(name: str, candidates: Iterable, min_score: int = DEFAULT_THRESHOLD, limit: int = 3,
                 exclude_id: Optional[int] = None):
    """candidates: objects with .id, .name and .normalized_name.
    Returns [{"id", "name", "score"}] sorted best-first (an exact normalized match scores 100)."""
    target = normalize_name(name)
    scored = []
    for c in candidates:
        if exclude_id is not None and c.id == exclude_id:
            continue
        score = similarity(target, c.normalized_name)
        if score >= min_score:
            scored.append({"id": c.id, "name": c.name, "score": score})
    scored.sort(key=lambda m: (-m["score"], m["name"]))
    return scored[:limit]

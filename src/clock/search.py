from difflib import SequenceMatcher
from typing import Any


def fuzzy_match(a: str, b: str) -> float:
    """Return similarity between 0 and 1."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def get_city_matches(data: Any, query: str, threshold: float = 0.8) -> list[dict[str, Any]]:
    """Get city entries that match the query string using fuzzy matching."""
    matches = []
    for entry in data:
        name = entry.get("name", "")
        similarity = fuzzy_match(query, name)
        if similarity > threshold or query in name.lower():
            matches.append(entry)

    return matches

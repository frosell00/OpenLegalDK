"""Identify common Danish and European legal citation formats in plain text.

This module identifies *patterns*; it does not validate citations against
primary legal sources, determine whether a provision is in force, or give
legal advice.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any


@dataclass(frozen=True)
class Citation:
    """A citation match with zero-based offsets into the source text."""

    kind: str
    text: str
    start: int
    end: int
    details: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Priorities are deliberate: longer, more specific patterns should win when
# they overlap a generic reference such as a standalone section symbol.
_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "ecli",
        re.compile(r"\bECLI:[A-Z]{2}:[A-Z0-9]+:[0-9]{4}:[A-Z0-9.:-]+\b", re.IGNORECASE),
    ),
    (
        "gdpr_article",
        re.compile(
            r"\b(?:GDPR|databeskyttelsesforordning(?:en|ens)?)\s+"
            r"(?:art\.?|article|artikel)\s*"
            r"(?P<article>\d+[a-z]?)"
            r"(?:(?:\s*\(\d+\))+|(?:,?\s*stk\.?\s*\d+))?"
            r"(?:(?:\s*\([a-z]\))|(?:,?\s*litra\s+[a-z]))?",
            re.IGNORECASE,
        ),
    ),
    (
        "eu_treaty_article",
        re.compile(
            r"\b(?P<treaty>TEUF|TEU|TFEU|TUE)\s+"
            r"(?:art\.?|article|artikel)\s*(?P<article>\d+[a-z]?)"
            r"(?:\s*\(\d+\))?",
            re.IGNORECASE,
        ),
    ),
    (
        "danish_act_section",
        re.compile(
            r"\b(?P<act>RPL|TL|KL|FVL|AFTL|STRFL|GRL|"
            r"retsplejelov(?:en|ens)?|tinglysningslov(?:en|ens)?|"
            r"konkurslov(?:en|ens)?|forvaltningslov(?:en|ens)?|"
            r"aftalelov(?:en|ens)?|straffelov(?:en|ens)?|"
            r"grundlov(?:en|ens)?)\s*"
            r"§{1,2}\s*(?P<section>\d+[a-z]?)"
            r"(?:\s*,?\s*stk\.?\s*\d+)?"
            r"(?:\s*,?\s*nr\.?\s*\d+)?",
            re.IGNORECASE,
        ),
    ),
    (
        "ufr_case",
        re.compile(
            r"\b(?:UfR|U)\.?\s*(?P<year>\d{4})[. ](?P<page>\d{1,5})"
            r"\s*(?P<court>H|Ø|V|SH|S)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "eu_case",
        re.compile(
            r"\b(?:(?:Case|Sag)\s+)?(?P<case>[CTF]-\d{1,5}/\d{2,4})\b",
            re.IGNORECASE,
        ),
    ),
    (
        "danish_section",
        re.compile(
            r"(?<!\w)§{1,2}\s*(?P<section>\d+[a-z]?)"
            r"(?:\s*,?\s*stk\.?\s*\d+)?"
            r"(?:\s*,?\s*nr\.?\s*\d+)?",
            re.IGNORECASE,
        ),
    ),
)


def find_citations(text: str) -> list[Citation]:
    """Return non-overlapping legal citation matches in original text order.

    Offsets are Python string offsets, using zero-based start and exclusive end.
    Longer and more-specific citations take precedence over generic ones.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    accepted: list[Citation] = []
    for kind, rule in _RULES:
        for match in rule.finditer(text):
            if any(match.start() < c.end and c.start < match.end() for c in accepted):
                continue
            details = {
                key: value for key, value in match.groupdict().items() if value is not None
            }
            accepted.append(
                Citation(kind, match.group(0), match.start(), match.end(), details)
            )
    return sorted(accepted, key=lambda c: (c.start, c.end))

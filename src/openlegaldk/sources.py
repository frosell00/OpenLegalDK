"""Trusted-document link resolution for selected, explicitly identified legal acts.

A source link is not proof that a citation is accurate or legally applicable.
The program does not fetch or scrape the linked website.
"""

from __future__ import annotations

from typing import Any

from .citations import Citation, find_citations


# EUR-Lex official document (not an unverified article-level fragment).
# Keep the CELEX identifier fixed: arbitrary input must never become a URL host
# or an unsupported legal document identifier.
_GDPR_CELEX = "32016R0679"
_EURLEX_BASE = "https://eur-lex.europa.eu/legal-content/"
_LANGUAGES = {"DA": "Artikel", "EN": "Article"}


def resolve_official_source(citation: Citation, *, language: str = "DA") -> dict[str, Any] | None:
    """Link a recognized GDPR article to its authoritative EUR-Lex document.

    Returns None for other kinds of citation or unknown GDPR article numbers.
    The URL is to the complete original regulation, *not* to a particular
    paragraph or point: EUR-Lex anchors may change without notice.

    ``language`` is the desired EUR-Lex language (``DA`` or ``EN``).
    """
    if not isinstance(language, str) or language.upper() not in _LANGUAGES:
        raise ValueError("language must be 'DA' or 'EN'")
    language = language.upper()

    if citation.kind != "gdpr_article":
        return None

    number = citation.details.get("article", "")
    if not number.isascii() or not number.isdecimal():
        return None
    article_number = int(number)
    # The 2016 GDPR contains articles 1–99. Reject out-of-range patterns.
    if not 1 <= article_number <= 99:
        return None

    return {
        "provider": "EUR-Lex",
        "title": "Regulation (EU) 2016/679 (GDPR)",
        "celex": _GDPR_CELEX,
        "article": article_number,
        "language": language,
        "url": f"{_EURLEX_BASE}{language}/TXT/?uri=CELEX%3A{_GDPR_CELEX}",
        "link_scope": "document",
        "find_on_page": f"{_LANGUAGES[language]} {article_number}",
        "verified_article": False,
    }


def find_citations_with_sources(text: str, *, language: str = "DA") -> list[dict[str, Any]]:
    """Extract citations and attach official-source links when supported.

    Each record contains the normal citation fields and, for supported GDPR
    references, an ``official_source`` object. No network calls occur.
    """
    if not isinstance(language, str) or language.upper() not in _LANGUAGES:
        raise ValueError("language must be 'DA' or 'EN'")
    result = []
    for citation in find_citations(text):
        item = citation.to_dict()
        source = resolve_official_source(citation, language=language)
        if source is not None:
            item["official_source"] = source
        result.append(item)
    return result

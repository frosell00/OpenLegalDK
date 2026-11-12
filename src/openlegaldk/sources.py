"""Trusted-document link resolution for selected, explicitly identified legal acts.

A source link is not proof that a citation is accurate or legally applicable.
Network article retrieval is opt-in and does not establish the current legal status.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .citations import Citation, find_citations
from .retrieval import SourceRetrievalError, download_gdpr_html, extract_article_text


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


def find_citations_with_sources(
    text: str,
    *,
    language: str = "DA",
    fetch_articles: bool = False,
    timeout: float = 12.0,
) -> list[dict[str, Any]]:
    """Extract legal citations and attach official links where supported.

    With ``fetch_articles=True``, make one opt-in EUR-Lex request and try to
    extract each referenced GDPR article. Retrieval errors are returned
    explicitly in the metadata instead of being hidden or invented away.
    The returned text is the *original* 2016 publication, not legal advice.
    """
    if not isinstance(language, str) or language.upper() not in _LANGUAGES:
        raise ValueError("language must be 'DA' or 'EN'")
    if not isinstance(fetch_articles, bool):
        raise TypeError("fetch_articles must be a boolean")
    language = language.upper()
    citations = find_citations(text)
    items = [citation.to_dict() for citation in citations]
    sources = [resolve_official_source(citation, language=language) for citation in citations]

    html = None
    download_error = None
    if fetch_articles and any(source is not None for source in sources):
        try:
            html = download_gdpr_html(language, timeout=timeout)
        except SourceRetrievalError as exc:
            download_error = str(exc)

    article_cache: dict[int, str | SourceRetrievalError] = {}
    retrieved_at = datetime.now(timezone.utc).isoformat() if html is not None else None
    for item, source in zip(items, sources):
        if source is None:
            continue
        item["official_source"] = source
        if not fetch_articles:
            continue
        if download_error:
            source["fetch_status"] = "unavailable"
            source["fetch_error"] = download_error
            continue
        article = source["article"]
        if article not in article_cache:
            try:
                article_cache[article] = extract_article_text(html, article, language=language)
            except SourceRetrievalError as exc:
                article_cache[article] = exc
        found = article_cache[article]
        if isinstance(found, SourceRetrievalError):
            source["fetch_status"] = "unavailable"
            source["fetch_error"] = str(found)
        else:
            source["fetch_status"] = "retrieved"
            source["article_text"] = found
            source["retrieved_at_utc"] = retrieved_at
            source["document_version"] = "original_oj_2016"
            source["verified_article"] = True  # Found in downloaded source, not a legal currency check
            source["current_law_verified"] = False
    return items

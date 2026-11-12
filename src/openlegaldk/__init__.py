"""OpenLegalDK: experimental open-source legal citation extraction."""

from .citations import Citation, find_citations
from .sources import find_citations_with_sources, resolve_official_source
from .retrieval import (
    SourceRetrievalError,
    download_gdpr_html,
    extract_article_text,
    fetch_gdpr_article,
)

__all__ = [
    "Citation",
    "find_citations",
    "find_citations_with_sources",
    "resolve_official_source",
    "SourceRetrievalError",
    "download_gdpr_html",
    "extract_article_text",
    "fetch_gdpr_article",
]
__version__ = "0.3.0"

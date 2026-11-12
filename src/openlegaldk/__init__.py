"""OpenLegalDK: experimental open-source legal citation extraction."""

from .citations import Citation, find_citations
from .sources import find_citations_with_sources, resolve_official_source

__all__ = [
    "Citation",
    "find_citations",
    "find_citations_with_sources",
    "resolve_official_source",
]
__version__ = "0.2.0"

"""Opt-in retrieval of EU GDPR articles from the official EUR-Lex HTML page.

Uses the stdlib and a fixed source URL. This is a best-effort HTML extractor;
EUR-Lex can throttle or block automated requests. Failing closed is intentional.
"""

from __future__ import annotations

from datetime import datetime, timezone
from html.parser import HTMLParser
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


GDPR_CELEX = "32016R0679"
EUR_LEX_HOST = "eur-lex.europa.eu"
MAX_RESPONSE_BYTES = 12 * 1024 * 1024
MAX_ARTICLE_CHARS = 50000


class SourceRetrievalError(RuntimeError):
    """Raised when the official text cannot be downloaded or isolated safely."""


def gdpr_html_url(language: str = "DA") -> str:
    """Return a fixed EUR-Lex HTML URL for the *original* GDPR regulation."""
    language = language.upper()
    if language not in {"DA", "EN"}:
        raise ValueError("language must be 'DA' or 'EN'")
    return (
        f"https://{EUR_LEX_HOST}/legal-content/{language}/TXT/HTML/"
        f"?uri=CELEX%3A{GDPR_CELEX}"
    )


def _trusted_url(url: str) -> bool:
    parsed = urlsplit(url)
    return (
        parsed.scheme == "https"
        and parsed.hostname == EUR_LEX_HOST
        and parsed.username is None
        and parsed.password is None
        and parsed.port in (None, 443)
    )


class _SafeRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _trusted_url(newurl):
            raise SourceRetrievalError("EUR-Lex redirected outside the official website")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download_gdpr_html(language: str = "DA", *, timeout: float = 12.0) -> str:
    """Download official HTML, bounded by time, size, and allowed domain.

    HTTP failures (including robot checks) raise SourceRetrievalError.
    The content is the original OJ document, not a current-law guarantee.
    """
    if timeout <= 0 or timeout > 60:
        raise ValueError("timeout must be greater than zero and at most 60 seconds")
    url = gdpr_html_url(language)
    request = Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": "OpenLegalDK/0.3 (+https://github.com/frosell00/OpenLegalDK)",
        },
    )
    try:
        opener = build_opener(_SafeRedirectHandler())
        with opener.open(request, timeout=timeout) as response:
            if not _trusted_url(response.geturl()):
                raise SourceRetrievalError("Response originated outside the official EUR-Lex website")
            content_type = response.headers.get("Content-Type", "").lower()
            if "html" not in content_type:
                raise SourceRetrievalError("EUR-Lex did not return an HTML document")
            declared_size = response.headers.get("Content-Length")
            if declared_size and int(declared_size) > MAX_RESPONSE_BYTES:
                raise SourceRetrievalError("EUR-Lex document exceeded the safe size limit")
            payload = response.read(MAX_RESPONSE_BYTES + 1)
            if len(payload) > MAX_RESPONSE_BYTES:
                raise SourceRetrievalError("EUR-Lex document exceeded the safe size limit")
    except SourceRetrievalError:
        raise
    except HTTPError as exc:
        raise SourceRetrievalError(f"EUR-Lex HTTP error {exc.code}") from exc
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        raise SourceRetrievalError("EUR-Lex could not be reached or returned an invalid response") from exc
    try:
        html = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise SourceRetrievalError("EUR-Lex HTML is not valid UTF-8") from exc
    if (
        "<html" not in html.lower()
        or "verify that you're not a robot" in html.lower()
        or "captcha" in html.lower()
        or "access denied" in html.lower()
    ):
        raise SourceRetrievalError("EUR-Lex returned an access check instead of legal text")
    return html


_BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "td", "th", "li", "br"}
_SKIP_TAGS = {"head", "script", "style", "noscript", "svg", "template"}
_ARTICLE_HEADING = re.compile(r"^(?:article|artikel)\s+([1-9]\d?)$", re.IGNORECASE)


class _VisibleBlocks(HTMLParser):
    """Lightweight HTML-to-block extraction preserving article heading classes."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[tuple[str, frozenset[str]]] = []
        self._text: list[str] = []
        self._classes: frozenset[str] = frozenset()
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._skip_depth:
            self._skip_depth += 1
            return
        if tag in _SKIP_TAGS:
            self._flush()
            self._skip_depth = 1
            return
        if tag in _BLOCK_TAGS:
            self._flush()
            classes = dict(attrs).get("class") or ""
            self._classes = frozenset(classes.lower().split())

    def handle_endtag(self, tag: str) -> None:
        if self._skip_depth:
            self._skip_depth -= 1
            return
        if tag in _BLOCK_TAGS:
            self._flush()

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self._text.append(data)

    def _flush(self) -> None:
        if self._text:
            text = re.sub(r"\s+", " ", "".join(self._text)).strip()
            if text:
                self.blocks.append((text, self._classes))
        self._text = []
        self._classes = frozenset()

    def close(self) -> None:
        super().close()
        self._flush()


def extract_article_text(html: str, article: int, *, language: str = "DA") -> str:
    """Extract a GDPR article from EUR-Lex HTML or fail without fabricating text.

    The extractor looks for a whole-line Article/Artikel N heading, ending at
    the next article heading. It filters out navigation/contents-only matches.
    The exact HTML layout can change; returned text must be reviewed by a human.
    """
    if not 1 <= article <= 99:
        raise ValueError("GDPR article must be in the range 1–99")
    if language.upper() not in {"DA", "EN"}:
        raise ValueError("language must be 'DA' or 'EN'")
    if not isinstance(html, str):
        raise TypeError("html must be a string")

    parser = _VisibleBlocks()
    parser.feed(html)
    parser.close()
    blocks = parser.blocks
    candidates: list[tuple[int, str]] = []
    for i, (block, classes) in enumerate(blocks):
        match = _ARTICLE_HEADING.fullmatch(block)
        if not match or int(match.group(1)) != article:
            continue
        next_article = next(
            (j for j in range(i + 1, len(blocks))
             if _ARTICLE_HEADING.fullmatch(blocks[j][0])),
            len(blocks),
        )
        body_blocks = [line for line, _ in blocks[i:next_article]]
        text = "\n".join(body_blocks).strip()
        # TOC entries are typically only article numbers/titles, not full text.
        if len(text) < 110 or not re.search(r"\b1[.]\s|\b1\s+[A-Za-zÆØÅæøå]", text):
            continue
        if len(text) > MAX_ARTICLE_CHARS:
            continue
        # EUR-Lex OJ HTML typically labels article headings with class ti-art.
        # Prefer those structural elements when the same heading appears in TOC.
        score = (100 if "ti-art" in classes else 0) + len(text)
        candidates.append((score, text))
    if not candidates:
        raise SourceRetrievalError(
            f"Could not isolate GDPR article {article} from EUR-Lex HTML; "
            "the page layout may have changed"
        )
    return max(candidates, key=lambda item: item[0])[1]


def fetch_gdpr_article(
    article: int, *, language: str = "DA", timeout: float = 12.0
) -> dict[str, Any]:
    """Download and extract original GDPR article text from EUR-Lex.

    No claims are made about a consolidated version or the legal effect of the
    extracted HTML. This operation requires a network connection.
    """
    html = download_gdpr_html(language, timeout=timeout)
    text = extract_article_text(html, article, language=language)
    return {
        "article": article,
        "language": language.upper(),
        "url": gdpr_html_url(language),
        "celex": GDPR_CELEX,
        "text": text,
        "document_version": "original_oj_2016",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "retrieved",
        "text_verified_against_current_law": False,
    }

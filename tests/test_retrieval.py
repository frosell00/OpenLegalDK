"""Offline tests: no real requests to EUR-Lex are made by this test suite."""

import io
import json
import unittest
from unittest.mock import patch
from email.message import Message
from urllib.error import HTTPError

from openlegaldk import (
    find_citations,
    find_citations_with_sources,
    SourceRetrievalError,
    extract_article_text,
    fetch_gdpr_article,
)
from openlegaldk.retrieval import (
    MAX_RESPONSE_BYTES,
    _trusted_url,
    download_gdpr_html,
    gdpr_html_url,
)
from openlegaldk.__main__ import main


SAMPLE_HTML = """<!DOCTYPE html><html><head><title>Regulation GDPR</title>
<script>Article 6 fake script</script></head><body>
<nav><p>Article 6</p><p>Lawfulness of processing</p><p>Article 7</p></nav>
<section>
<p class="ti-art">Article&nbsp;5</p>
<p class="sti-art">Principles relating to processing</p>
<p class="normal">1. Personal data shall be fair and lawful and transparent.</p>
<p class="ti-art">Article&nbsp;<span>6</span></p>
<p class="sti-art">Lawfulness of processing</p>
<p class="normal">1. Processing shall be lawful only if at least one of the following applies:</p>
<table><tr><td>(a)</td><td>the data subject has given consent to processing</td></tr>
<tr><td>(f)</td><td>processing is necessary for the legitimate interests pursued by the controller or a third party</td></tr></table>
<p class="normal">2. Member States may maintain or introduce more specific provisions.</p>
<p class="ti-art">Article 7</p>
<p class="sti-art">Conditions for consent</p>
<p>1. Consent must be demonstrable.</p>
</section></body></html>"""

DA_HTML = """<html><head></head><body>
<p class='ti-art'>Artikel 6</p><p class='sti-art'>Lovlig behandling</p>
<p>1. Behandling er kun lovlig, hvis mindst ét af følgende forhold gør sig gældende:</p>
<p>a) Den registrerede har givet samtykke.</p>
<p>f) Behandling er nødvendig for at forfølge en legitim interesse med passende afvejning.</p>
<p>2. Medlemsstaterne kan opretholde eller indføre mere specifikke bestemmelser.</p>
<p class='ti-art'>Artikel 7</p><p>1. Krav til samtykke.</p>
</body></html>"""


class FakeResponse:
    def __init__(self, body, content_type="text/html; charset=utf-8", url=None, length=None):
        self.body = io.BytesIO(body)
        self.headers = Message()
        self.headers["Content-Type"] = content_type
        if length is not None:
            self.headers["Content-Length"] = str(length)
        self.url = url or gdpr_html_url("EN")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.body.close()

    def geturl(self):
        return self.url

    def read(self, length=-1):
        return self.body.read(length)


class RetrievalTests(unittest.TestCase):
    def test_extract_article_skips_table_of_contents_and_script(self):
        result = extract_article_text(SAMPLE_HTML, 6, language="EN")
        self.assertIn("Lawfulness of processing", result)
        self.assertIn("legitimate interests", result)
        self.assertIn("Processing shall be lawful", result)
        self.assertNotIn("Article 7", result)
        self.assertNotIn("Article 6 fake script", result)

    def test_extract_danish_article(self):
        result = extract_article_text(DA_HTML, 6)
        self.assertIn("Artikel 6", result)
        self.assertIn("Lovlig behandling", result)
        self.assertNotIn("Artikel 7", result)

    def test_reject_unrecognized_layout(self):
        with self.assertRaises(SourceRetrievalError):
            extract_article_text("<html><body><p>Article 6</p><p>Contents</p></body></html>", 6)

    def test_reject_invalid_article_and_language(self):
        with self.assertRaises(ValueError):
            extract_article_text(SAMPLE_HTML, 100)
        with self.assertRaises(ValueError):
            extract_article_text(SAMPLE_HTML, 6, language="FR")

    def test_fetch_api_with_mocked_official_document(self):
        with patch("openlegaldk.retrieval.download_gdpr_html", return_value=SAMPLE_HTML):
            result = fetch_gdpr_article(6, language="EN")
        self.assertEqual(result["status"], "retrieved")
        self.assertFalse(result["text_verified_against_current_law"])
        self.assertIn("legitimate interests", result["text"])
        self.assertEqual(result["document_version"], "original_oj_2016")

    def test_citation_details_have_paragraph_and_point(self):
        da, en = [find_citations(s)[0] for s in (
            "GDPR artikel 6, stk. 1, litra f", "GDPR Article 6(1)(f)"
        )]
        self.assertEqual(da.details, en.details)
        self.assertEqual(da.details, {"article": "6", "paragraph": "1", "point": "f"})

    def test_fetch_once_for_multiple_citations_and_cache_article(self):
        with patch("openlegaldk.sources.download_gdpr_html", return_value=SAMPLE_HTML) as request:
            found = find_citations_with_sources(
                "GDPR Article 6(1)(f). Also GDPR Article 6(1)(a). GDPR Article 7",
                language="EN", fetch_articles=True,
            )
        self.assertEqual(request.call_count, 1)
        self.assertEqual([x["official_source"]["fetch_status"] for x in found],
                         ["retrieved", "retrieved", "unavailable"])
        self.assertEqual(found[0]["official_source"]["article_text"],
                         found[1]["official_source"]["article_text"])
        self.assertNotIn("article_text", found[2]["official_source"])

    def test_network_failure_preserves_links(self):
        with patch("openlegaldk.sources.download_gdpr_html", side_effect=SourceRetrievalError("HTTP 403")):
            found = find_citations_with_sources("GDPR artikel 6", fetch_articles=True)
        source = found[0]["official_source"]
        self.assertEqual(source["fetch_status"], "unavailable")
        self.assertFalse(source["verified_article"])
        self.assertEqual(source["fetch_error"], "HTTP 403")
        self.assertIn("32016R0679", source["url"])

    def test_no_network_without_opt_in(self):
        with patch("openlegaldk.sources.download_gdpr_html") as network:
            found = find_citations_with_sources("GDPR artikel 6")
        network.assert_not_called()
        self.assertNotIn("fetch_status", found[0]["official_source"])

    def test_reject_unsafe_redirect_targets(self):
        self.assertTrue(_trusted_url(gdpr_html_url("EN")))
        for url in [
            "http://eur-lex.europa.eu/a", "https://example.org/a",
            "https://eur-lex.europa.eu.example.org/a",
            "https://u:p@eur-lex.europa.eu/a", "https://eur-lex.europa.eu:445/a",
        ]:
            self.assertFalse(_trusted_url(url), url)

    def test_download_html_with_mocked_response(self):
        response = FakeResponse(SAMPLE_HTML.encode("utf-8"))
        with patch("openlegaldk.retrieval.build_opener") as opener:
            opener.return_value.open.return_value = response
            text = download_gdpr_html("EN")
        self.assertIn("Lawfulness of processing", text)

    def test_download_rejects_robot_page(self):
        response = FakeResponse(b"<html>Verify that you're not a robot</html>")
        with patch("openlegaldk.retrieval.build_opener") as opener:
            opener.return_value.open.return_value = response
            with self.assertRaises(SourceRetrievalError):
                download_gdpr_html("EN")

    def test_download_rejects_oversize(self):
        response = FakeResponse(b"<html>hello</html>", length=MAX_RESPONSE_BYTES + 1)
        with patch("openlegaldk.retrieval.build_opener") as opener:
            opener.return_value.open.return_value = response
            with self.assertRaises(SourceRetrievalError):
                download_gdpr_html("EN")

    def test_download_rejects_http_errors(self):
        with patch("openlegaldk.retrieval.build_opener") as opener:
            opener.return_value.open.side_effect = HTTPError(gdpr_html_url(), 403, "Forbidden", {}, None)
            with self.assertRaisesRegex(SourceRetrievalError, "403"):
                download_gdpr_html("DA")

    def test_cli_outputs_article_text_when_fetch_succeeds(self):
        with patch("sys.argv", ["openlegaldk", "--fetch-articles", "--language", "DA"]), \
             patch("sys.stdin", io.StringIO("GDPR artikel 6")), \
             patch("sys.stdout", new_callable=io.StringIO) as output, \
             patch("openlegaldk.sources.download_gdpr_html", return_value=DA_HTML):
            self.assertEqual(main(), 0)
        result = json.loads(output.getvalue())
        self.assertIn("Lovlig behandling", result[0]["official_source"]["article_text"])

    def test_strict_fetch_returns_nonzero_but_outputs_json(self):
        with patch("sys.argv", ["openlegaldk", "--fetch-articles", "--strict-fetch"]), \
             patch("sys.stdin", io.StringIO("GDPR artikel 6")), \
             patch("sys.stdout", new_callable=io.StringIO) as output, \
             patch("openlegaldk.sources.download_gdpr_html", side_effect=SourceRetrievalError("blocked")):
            self.assertEqual(main(), 2)
        result = json.loads(output.getvalue())
        self.assertEqual(result[0]["official_source"]["fetch_status"], "unavailable")


if __name__ == "__main__":
    unittest.main()

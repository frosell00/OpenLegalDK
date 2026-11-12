import json
import subprocess
import sys
import unittest
from unittest.mock import patch

from openlegaldk import find_citations, find_citations_with_sources, resolve_official_source
from openlegaldk.__main__ import main


class SourcesTests(unittest.TestCase):
    def test_danish_gdpr_article6_link(self):
        matches = find_citations_with_sources("GDPR artikel 6, stk. 1, litra f")
        self.assertEqual(len(matches), 1)
        source = matches[0]["official_source"]
        self.assertEqual(source["celex"], "32016R0679")
        self.assertEqual(source["article"], 6)
        self.assertEqual(source["language"], "DA")
        self.assertEqual(source["find_on_page"], "Artikel 6")
        self.assertEqual(
            source["url"],
            "https://eur-lex.europa.eu/legal-content/DA/TXT/?uri=CELEX%3A32016R0679",
        )
        self.assertEqual(source["link_scope"], "document")
        self.assertFalse(source["verified_article"])

    def test_english_version(self):
        matches = find_citations_with_sources("GDPR Article 6(1)(f)", language="EN")
        self.assertEqual(matches[0]["official_source"]["find_on_page"], "Article 6")
        self.assertIn("/EN/TXT/", matches[0]["official_source"]["url"])

    def test_no_link_for_other_law(self):
        matches = find_citations_with_sources("RPL § 478 and C-12/25")
        self.assertEqual(len(matches), 2)
        self.assertTrue(all("official_source" not in item for item in matches))

    def test_invalid_article_no_link(self):
        matches = find_citations_with_sources("GDPR artikel 100")
        self.assertEqual(len(matches), 1)
        self.assertNotIn("official_source", matches[0])

    def test_empty_reference_no_link(self):
        self.assertIsNone(resolve_official_source(find_citations("KL § 70")[0]))

    def test_invalid_language(self):
        with self.assertRaises(ValueError):
            find_citations_with_sources("GDPR artikel 6", language="XX")

    def test_json_cli_links_by_default(self):
        result = subprocess.run(
            [sys.executable, "-m", "openlegaldk", "--pretty"],
            input="GDPR artikel 6 og RPL § 478",
            capture_output=True, text=True, check=True,
        )
        data = json.loads(result.stdout)
        self.assertEqual(len(data), 2)
        self.assertIn("official_source", data[0])
        self.assertNotIn("official_source", data[1])

    def test_cli_no_links_legacy_output(self):
        result = subprocess.run(
            [sys.executable, "-m", "openlegaldk", "--no-links"],
            input="GDPR Article 6(1)(f)", capture_output=True, text=True, check=True,
        )
        self.assertNotIn("official_source", json.loads(result.stdout)[0])

    def test_cli_open_first_source(self):
        with patch("sys.argv", ["openlegaldk", "--open-first-source"]), \
             patch("sys.stdin", new=__import__("io").StringIO("GDPR artikel 6")), \
             patch("webbrowser.open_new_tab") as browser, \
             patch("sys.stdout", new=__import__("io").StringIO()):
            self.assertEqual(main(), 0)
            browser.assert_called_once_with(
                "https://eur-lex.europa.eu/legal-content/DA/TXT/?uri=CELEX%3A32016R0679"
            )


if __name__ == "__main__":
    unittest.main()

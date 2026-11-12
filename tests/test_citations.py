import json
import subprocess
import sys
import unittest

from openlegaldk import find_citations


class CitationTests(unittest.TestCase):
    def test_mixed_danish_eu_citations(self):
        sample = (
            "RPL § 478, stk. 1, nr. 4; GDPR Article 6(1)(f); "
            "TEUF artikel 267; U 2024.123 H; C-12/25; "
            "ECLI:EU:C:2020:559"
        )
        matches = find_citations(sample)
        self.assertEqual(
            [c.kind for c in matches],
            [
                "danish_act_section", "gdpr_article", "eu_treaty_article",
                "ufr_case", "eu_case", "ecli",
            ],
        )
        self.assertEqual([sample[c.start:c.end] for c in matches], [c.text for c in matches])
        self.assertEqual(matches[1].details["article"], "6")

    def test_danish_gdpr(self):
        matches = find_citations("GDPR artikel 6, stk. 1, litra f")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].text, "GDPR artikel 6, stk. 1, litra f")

    def test_generic_section_not_duplicated(self):
        matches = find_citations("Forvaltningsloven § 19 og § 22")
        self.assertEqual([c.kind for c in matches], ["danish_act_section", "danish_section"])
        self.assertEqual([c.text for c in matches], ["Forvaltningsloven § 19", "§ 22"])

    def test_eu_case_with_context(self):
        matches = find_citations("See Case C-311/18 and Sag T-42/19.")
        self.assertEqual([c.text for c in matches], ["Case C-311/18", "Sag T-42/19"])

    def test_non_matches(self):
        self.assertEqual(find_citations("Ordinary paragraphs without legal citations."), [])

    def test_type_validation(self):
        with self.assertRaises(TypeError):
            find_citations(None)

    def test_json_output(self):
        result = subprocess.run(
            [sys.executable, "-m", "openlegaldk", "--pretty"],
            input="KL § 70 og TEUF artikel 267",
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        self.assertEqual([c["kind"] for c in data], ["danish_act_section", "eu_treaty_article"])


if __name__ == "__main__":
    unittest.main()

"""Synthetic regression corpus: pattern recognition, not legal validity."""

import unittest

from openlegaldk import find_citations


# (input, expected [(kind, matched_text), ...])
CASES = (
    ("RPL § 478, stk. 1, nr. 4", [("danish_act_section", "RPL § 478, stk. 1, nr. 4")]),
    ("Forvaltningsloven § 19", [("danish_act_section", "Forvaltningsloven § 19")]),
    ("KL § 70 og § 71", [("danish_act_section", "KL § 70"), ("danish_section", "§ 71")]),
    ("GDPR artikel 6, stk. 1, litra f", [("gdpr_article", "GDPR artikel 6, stk. 1, litra f")]),
    ("GDPR Article 6(1)(f)", [("gdpr_article", "GDPR Article 6(1)(f)")]),
    ("databeskyttelsesforordningen artikel 5", [("gdpr_article", "databeskyttelsesforordningen artikel 5")]),
    ("TEUF artikel 267", [("eu_treaty_article", "TEUF artikel 267")]),
    ("TFEU Article 267", [("eu_treaty_article", "TFEU Article 267")]),
    ("U 2024.123 H", [("ufr_case", "U 2024.123 H")]),
    ("Sag C-12/25", [("eu_case", "Sag C-12/25")]),
    ("ECLI:EU:C:2020:559", [("ecli", "ECLI:EU:C:2020:559")]),
    ("Ingen juridiske henvisninger her.", []),
    ("§ 22 og § 23", [("danish_section", "§ 22"), ("danish_section", "§ 23")]),
)


class CitationRegressionTests(unittest.TestCase):
    def test_corpus(self):
        for source, expected in CASES:
            with self.subTest(source=source):
                found = find_citations(source)
                self.assertEqual([(c.kind, c.text) for c in found], expected)
                self.assertEqual([source[c.start:c.end] for c in found], [c.text for c in found])
                self.assertEqual([(c.start, c.end) for c in found],
                                 sorted((c.start, c.end) for c in found))

    def test_unicode_offsets_and_nonoverlap(self):
        source = "⚖️ GDPR artikel 6, stk. 1, litra f — RPL § 478"
        found = find_citations(source)
        self.assertEqual(len(found), 2)
        self.assertEqual([source[c.start:c.end] for c in found], [c.text for c in found])
        self.assertTrue(all(left.end <= right.start for left, right in zip(found, found[1:])))

    def test_gdpr_normalized_metadata(self):
        for source in ("GDPR artikel 6, stk. 1, litra f", "GDPR Article 6(1)(f)"):
            with self.subTest(source=source):
                details = find_citations(source)[0].details
                self.assertEqual(details["article"], "6")
                self.assertEqual(details["paragraph"], "1")
                self.assertEqual(details["point"], "f")


if __name__ == "__main__":
    unittest.main()

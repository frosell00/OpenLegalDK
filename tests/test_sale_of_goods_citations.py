"""Regression tests for syntactic Købeloven citations (not legal verification)."""

import unittest

from openlegaldk import find_citations, find_citations_with_sources


class SaleOfGoodsCitationTests(unittest.TestCase):
    def test_abbreviation_and_full_name(self):
        for reference in ("KBL § 17", "Købeloven § 17", "købelovens § 17"):
            with self.subTest(reference=reference):
                matches = find_citations(reference)
                self.assertEqual(len(matches), 1)
                self.assertEqual(matches[0].kind, "danish_act_section")
                self.assertEqual(matches[0].text, reference)
                self.assertEqual(matches[0].details["section"], "17")
                self.assertEqual(matches[0].start, 0)
                self.assertEqual(matches[0].end, len(reference))

    def test_longer_reference_and_generic_section(self):
        source = "KBL § 17, stk. 1, nr. 2 og § 18"
        matches = find_citations(source)
        self.assertEqual([m.kind for m in matches], [
            "danish_act_section", "danish_section",
        ])
        self.assertEqual([m.text for m in matches], [
            "KBL § 17, stk. 1, nr. 2", "§ 18",
        ])

    def test_no_fabricated_official_source(self):
        matches = find_citations_with_sources("Købeloven § 17")
        self.assertEqual(len(matches), 1)
        self.assertNotIn("official_source", matches[0])

    def test_unrelated_word_is_not_matched(self):
        self.assertEqual(find_citations("Minikøbeloven § 17"), [])


if __name__ == "__main__":
    unittest.main()

# OpenLegalDK ⚖️

**Open-source Python tools for working with Danish and European legal references.**

OpenLegalDK is an early-stage, experimental legal technology project initiated by a law student at the University of Copenhagen. It aims to make legal citations easier to extract, reuse, and eventually connect to public legal information across Danish and European sources.

## What works today

Version 0.1.0 includes a dependency-free Python citation extractor covering:

| Citation family | Example |
| --- | --- |
| Danish statutes | RPL § 478, stk. 1, nr. 4 |
| Danish sections | § 22 |
| GDPR | GDPR Article 6(1)(f) |
| EU treaties | TEUF artikel 267 |
| Danish case reports | U 2024.123 H |
| EU court cases | C-12/25 |
| ECLI | ECLI:EU:C:2020:559 |

These are regular-expression-based detections, NOT verified references or links to court databases. The software does not establish whether any cited provision or case exists, is current, or is legally relevant.

## Quick start

Requires Python 3.10+.

~~~bash
python -m pip install -e .
~~~

Python API:

~~~python
from openlegaldk import find_citations

text = "See RPL § 478, stk. 1, nr. 4 and GDPR Article 6(1)(f)."
for citation in find_citations(text):
    print(citation.kind, citation.text, citation.start, citation.end)
~~~

JSON CLI, reading from stdin:

~~~bash
echo 'TEUF artikel 267 og C-12/25' | python -m openlegaldk --pretty
~~~

Or supply a UTF-8 text file:

~~~bash
python -m openlegaldk my_legal_text.txt --pretty
~~~

## Roadmap

- [x] Python library and JSON CLI
- [x] Initial Danish statute, GDPR, EU treaty, case-number, and ECLI patterns
- [x] Unit tests and GitHub Actions configuration
- [ ] More statute abbreviations and robust citation grammar
- [ ] Confidence scores and richer normalized metadata
- [ ] Optional links to Retsinformation, EUR-Lex and CURIA, with verification
- [ ] Versioned benchmark corpus and regression tests
- [ ] Community review from legal practitioners and developers

## Testing

~~~bash
python -m unittest discover -s tests -v
~~~

CI runs on Python 3.10, 3.12, and 3.13.

## Why open source?

Legal source formats should be easier for developers, researchers and students to work with without relying entirely on proprietary databases. This project explores small, practical, reusable components for legal research applications and future legal AI systems.

**Project status:** experimental, not production-ready. No external users, downloads or community contributors are claimed. Contributions are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).

## Disclaimer

This software is for experimentation and legal information processing, **not legal advice**. Verify every legal reference independently against authoritative sources.

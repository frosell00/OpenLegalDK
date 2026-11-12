# OpenLegalDK ⚖️

**Open-source tools for working with Danish and European legal references.**

[![Tests](https://github.com/frosell00/OpenLegalDK/actions/workflows/tests.yml/badge.svg)](https://github.com/frosell00/OpenLegalDK/actions/workflows/tests.yml)
![Status](https://img.shields.io/badge/status-experimental-orange)
![License](https://img.shields.io/badge/license-MIT-green)

OpenLegalDK is an **early-stage, experimental legal technology project** initiated by a law student at the **University of Copenhagen**. Its goal is to make legal citations easier to extract, reuse, and eventually connect to public legal information across Danish and European sources.

Legal texts contain many reference formats, from Danish statute sections to EUR-Lex provisions and judgments of European courts. A small, openly licensed Python toolkit can help developers and students build better workflows around them.

## What works today

Version **0.3.0** includes a dependency-free Python citation extractor **and official EUR-Lex document links for GDPR article citations**. It supports common patterns such as:

| Citation family | Examples |
| --- | --- |
| Danish statutes | `RPL § 478, stk. 1, nr. 4`, `Forvaltningsloven § 19` |
| Danish section references | `§ 22`, `§ 37, stk. 2` |
| GDPR | `GDPR Article 6(1)(f)`, `GDPR artikel 6, stk. 1, litra f` |
| EU treaties | `TEUF artikel 267`, `TFEU Article 267` |
| Danish case reports | `U 2024.123 H` |
| EU court cases | `C-12/25`, `Case C-311/18` |
| European Case Law Identifier | `ECLI:EU:C:2020:559` |

**Current limitation:** These are regular-expression-based detections, **not verified references or links to court databases** (except document-level GDPR EUR-Lex links). Some formats may be missed or falsely matched. Legal materials evolve; the software does not establish whether any cited provision or case exists, is current, or is legally relevant.

## Quick start

Requires Python 3.10 or newer.

```bash
python -m pip install -e .
```

Use the Python API:

```python
from openlegaldk import find_citations

text = "See RPL § 478, stk. 1, nr. 4 and GDPR Article 6(1)(f)."
for citation in find_citations(text):
    print(citation.kind, citation.text, citation.start, citation.end)
```

### Official EUR-Lex links for GDPR citations

When OpenLegalDK encounters a citation such as `GDPR artikel 6, stk. 1, litra f`, the CLI now adds an `official_source` object pointing to the **official EUR-Lex version of Regulation (EU) 2016/679**. This works without an API key or a network request from the parser.

```bash
echo 'GDPR artikel 6, stk. 1, litra f' | python -m openlegaldk --pretty
```

Example excerpt from the result:

```json
{
  "kind": "gdpr_article",
  "text": "GDPR artikel 6, stk. 1, litra f",
  "official_source": {
    "provider": "EUR-Lex",
    "celex": "32016R0679",
    "article": 6,
    "language": "DA",
    "url": "https://eur-lex.europa.eu/legal-content/DA/TXT/?uri=CELEX%3A32016R0679",
    "link_scope": "document",
    "find_on_page": "Artikel 6",
    "verified_article": false
  }
}
```

The excerpt omits some metadata fields for readability. The link opens the **full original GDPR**, so use `find_on_page` to locate the relevant article. It is deliberately **not** claimed to be a deep link to a particular paragraph or point. The URL is based on a known official CELEX identifier, not on a live legal-status or citation check.

Open the first supported source in your default browser:

```bash
echo 'GDPR Article 6(1)(f)' | python -m openlegaldk --open-first-source
```

Get an English source, or preserve the old citation-only JSON format:

```bash
echo 'GDPR Article 6(1)(f)' | python -m openlegaldk --language EN
echo 'GDPR Article 6(1)(f)' | python -m openlegaldk --no-links
```

Python API:

```python
from openlegaldk import find_citations_with_sources
matches = find_citations_with_sources("GDPR artikel 6", language="DA")
print(matches[0]["official_source"]["url"])
```

By default, this feature **only links** to official text; it does **not download, scrape, or validate** the article, check its legal status, or establish which provision applies in a specific case. Source links are currently generated only for GDPR articles 1–99. The optional `--fetch-articles` mode described below attempts retrieval from EUR-Lex, but does not verify whether the text is current or applicable.

Or pipe text into the CLI for UTF-8 JSON output:

```bash
echo 'TEUF artikel 267 og C-12/25' | python -m openlegaldk --pretty
```

You may also supply a UTF-8 text file:

```bash
python -m openlegaldk my_legal_text.txt --pretty
```

### Optional retrieval of the actual GDPR article text (v0.3.0)

On request, OpenLegalDK can try to download the **original 2016 Official Journal text** from EUR-Lex, locate the cited GDPR article, and return it alongside the link. This is **opt-in** because it makes a network request. It may not work if EUR-Lex restricts automated retrieval or changes its HTML layout. When fetching fails, the JSON still includes the official link and an explicit `fetch_status: unavailable` error instead of fabricated text.

```bash
echo 'GDPR artikel 6, stk. 1, litra f' | python -m openlegaldk --fetch-articles --pretty
```

To retrieve English text or make failures produce a nonzero exit status:

```bash
echo 'GDPR Article 6(1)(f)' | python -m openlegaldk --fetch-articles --language EN
echo 'GDPR artikel 6' | python -m openlegaldk --fetch-articles --strict-fetch
```

Python API:

```python
from openlegaldk import find_citations_with_sources

found = find_citations_with_sources('GDPR artikel 6, stk. 1, litra f', fetch_articles=True)
source = found[0]['official_source']
if source.get('fetch_status') == 'retrieved':
    print(source['article_text'])
else:
    print(source['url'], source.get('fetch_error'))
```

A successful response includes an explicit UTC retrieval time and `document_version: original_oj_2016`. It does **not** validate current applicability, identify the latest consolidated text, verify any quoted paragraph, or guarantee an official article-level hyperlink. Only the original full article is extracted. The `details` field now normalizes GDPR paragraph and point numbers separately (e.g. `paragraph: 1`, `point: f`).

### Browser demo

The [`docs/`](docs/) directory includes a standalone, zero-dependency browser demo. It detects citations **locally**, highlights matches and offers links to EUR-Lex for GDPR articles. It does **not** fetch legal texts, upload user text, or provide legal advice. Open `docs/index.html` through a local static HTTP server (for example `python -m http.server 8000` from the repository root and then visit `/docs/`).

The JavaScript parser is a **separate experimental demonstration**. It is not guaranteed to match the Python library for all citation formats. Its tests can be run with Node 22+ using `cd docs && npm test`.

## Project roadmap

- [x] Initial Python library and JSON CLI
- [x] Support common Danish statute, GDPR, EU treaty, case number, and ECLI patterns
- [x] Unit tests and GitHub Actions CI configuration
- [ ] Add additional statute abbreviations and robust citation grammar
- [ ] Build confidence scoring and richer normalized metadata
- [x] Add official document-level EUR-Lex links for GDPR articles (no live validation)
- [x] Add optional original-article text retrieval from EUR-Lex, with failure handling
- [ ] Improve live HTML compatibility and support consolidated texts after verifying official formats
- [ ] Add source resolution for Retsinformation and CURIA
- [x] Publish a local-only browser demo in `docs/`
- [ ] Add a documented, versioned benchmark corpus and regression tests
- [ ] Invite review from legal practitioners and open-source contributors

## Why open source?

Legal source formats should not be difficult to handle simply because you do not have a paid database subscription. This project explores small, practical, reusable tools as an alternative foundation for legal research applications, classroom projects, and future legal AI systems.

The project **does not claim production readiness, users, downloads, or external contributors**. Anyone interested in legal information infrastructure is welcome to propose a fix or contribute tests.

## Testing

```bash
python -m unittest discover -s tests -v
```

CI is set up in `.github/workflows/tests.yml` to test Python 3.10, 3.12, 3.13 and the browser demo on Node 22.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Please use short, synthetic citation examples in bug reports and tests and avoid uploading confidential or personal legal documents.

## License

MIT — see [LICENSE](LICENSE).

## Disclaimer

This software is for experimentation and legal information processing. It is **not legal advice**, a replacement for primary sources, or a verified citation database. Verify all legal references independently.

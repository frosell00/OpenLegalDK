/** Experimental browser demo for OpenLegalDK, no analytics or server calls. */
export const EUR_LEX_BASE = 'https://eur-lex.europa.eu/legal-content/';
const PATTERNS = [
  {
    kind: 'gdpr_article', label: 'GDPR',
    pattern: /\b(?:GDPR|databeskyttelsesforordningen)\s+(?:artikel|article|art\.)\s*(\d{1,3})(?:\s*\(\s*(\d+)\s*\)|\s*,?\s*stk\.?\s*(\d+))?(?:\s*\(\s*([a-z])\s*\)|\s*,?\s*litra\s+([a-z]))?/gi,
    resolver: (m, lang) => {
      const article = Number(m[1]);
      if (article < 1 || article > 99) return null;
      return {
        provider: 'EUR-Lex', article, celex: '32016R0679',
        url: `${EUR_LEX_BASE}${lang}/TXT/?uri=CELEX%3A32016R0679`,
        find_on_page: `${lang === 'DA' ? 'Artikel' : 'Article'} ${article}`,
        verified_article: false, link_scope: 'document',
      };
    },
  },
  { kind: 'danish_act_section', label: 'Dansk lov', pattern: /\b(?:RPL|TL|KL|FVL|AFTL|STRFL|GRL|retsplejeloven|konkursloven|forvaltningsloven|tinglysningsloven)\s*§\s*\d+[a-z]?(?:\s*,?\s*stk\.?\s*\d+)?(?:\s*,?\s*nr\.?\s*\d+)?/gi },
  { kind: 'eu_treaty_article', label: 'EU-traktat', pattern: /\b(?:TEUF|TEU|TFEU)\s+(?:artikel|article|art\.)\s*\d+/gi },
  { kind: 'ecli', label: 'ECLI', pattern: /\bECLI:[A-Z]{2}:[A-Z0-9]+:\d{4}:[A-Z0-9.:-]+\b/gi },
  { kind: 'eu_case', label: 'EU-domstol', pattern: /\b(?:Case|Sag)?\s*\b[CTF]-\d{1,5}\/\d{2,4}\b/gi },
  { kind: 'ufr_case', label: 'Dansk dom', pattern: /\b(?:UfR|U)\.?\s*\d{4}[. ]\d{1,5}\s*(?:H|Ø|V|SH|S)\b/gi },
  { kind: 'danish_section', label: 'Paragraf', pattern: /(?<!\w)§{1,2}\s*\d+[a-z]?(?:\s*,?\s*stk\.?\s*\d+)?/gi },
];

/** Return non-overlapping citation objects in source order, zero-based offsets. */
export function findCitations(text, language = 'DA') {
  if (typeof text !== 'string') throw new TypeError('Text must be a string');
  if (!['DA', 'EN'].includes(language)) throw new TypeError('Language must be DA or EN');
  const matches = [];
  for (const rule of PATTERNS) {
    for (const match of text.matchAll(rule.pattern)) {
      const start = match.index;
      const end = start + match[0].length;
      if (matches.some((prev) => start < prev.end && end > prev.start)) continue;
      const result = { kind: rule.kind, label: rule.label, text: match[0], start, end };
      if (rule.kind === 'gdpr_article') {
        result.details = { article: match[1] };
        const paragraph = match[2] || match[3];
        const point = match[4] || match[5];
        if (paragraph) result.details.paragraph = paragraph;
        if (point) result.details.point = point.toLowerCase();
      }
      const source = rule.resolver?.(match, language);
      if (source) result.official_source = source;
      matches.push(result);
    }
  }
  return matches.sort((a, b) => a.start - b.start);
}

function el(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function renderHighlights(container, text, matches) {
  container.replaceChildren();
  let cursor = 0;
  for (const match of matches) {
    container.append(document.createTextNode(text.slice(cursor, match.start)));
    const mark = el('mark', 'highlight', match.text);
    mark.title = match.label;
    container.append(mark);
    cursor = match.end;
  }
  container.append(document.createTextNode(text.slice(cursor)));
}

function renderResults(container, matches) {
  container.replaceChildren();
  for (const match of matches) {
    const item = el('article', 'result');
    const heading = el('div', 'result-title');
    heading.append(el('strong', '', match.text), el('span', 'chip', match.label));
    item.append(heading);
    if (match.official_source) {
      const link = el('a', 'source-link', 'Åbn GDPR på EUR-Lex ↗');
      link.href = match.official_source.url;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      item.append(link);
      item.append(el('small', 'muted', `Find ${match.official_source.find_on_page} · Dokumentlink, ikke juridisk validering`));
    } else {
      item.append(el('small', 'muted', 'Henvisning genkendt · Intet verificeret kildelink endnu'));
    }
    container.append(item);
  }
}

function main() {
  const input = document.getElementById('input');
  const lang = document.getElementById('lang');
  const hits = document.getElementById('hits');
  const highlights = document.getElementById('highlights');
  const results = document.getElementById('results');
  const sample = document.getElementById('sample');
  const copy = document.getElementById('copy');
  const status = document.getElementById('status');
  let current = [];
  const analyze = () => {
    const text = input.value.slice(0, 30000);
    current = findCitations(text, lang.value);
    hits.textContent = `${current.length} fund`;
    renderHighlights(highlights, text, current);
    renderResults(results, current);
    status.textContent = 'Analysen foregår lokalt i din browser. Ingen tekst sendes til en server.';
  };
  input.addEventListener('input', analyze);
  lang.addEventListener('change', analyze);
  sample.addEventListener('click', () => {
    input.value = 'Efter RPL § 478, stk. 1 kan der ske tvangsfuldbyrdelse. GDPR artikel 6, stk. 1, litra f og TEUF artikel 267 kan være relevante. Se også C-12/25.';
    analyze();
  });
  copy.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(current, null, 2));
      status.textContent = 'JSON kopieret.';
    } catch {
      status.textContent = 'Kopiering kræver muligvis HTTPS eller browser-tilladelse.';
    }
  });
  analyze();
}

if (typeof document !== 'undefined') main();

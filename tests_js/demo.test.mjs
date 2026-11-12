import assert from 'node:assert/strict';
import test from 'node:test';
import { findCitations } from '../docs/app.js';

test('GDPR link and correct Danish paragraph metadata', () => {
  const [m] = findCitations('GDPR artikel 6, stk. 1, litra f');
  assert.equal(m.details.article, '6');
  assert.equal(m.details.paragraph, '1');
  assert.equal(m.details.point, 'f');
  assert.equal(m.official_source.celex, '32016R0679');
  assert.equal(m.official_source.verified_article, false);
});
test('official EN link', () => {
  const [m] = findCitations('GDPR Article 6(1)(f)', 'EN');
  assert.match(m.official_source.url, /\/EN\/TXT\//);
});
test('avoid duplicate generic sections', () => {
  const matches = findCitations('RPL § 478 og § 22');
  assert.deepEqual(matches.map((m) => m.kind), ['danish_act_section','danish_section']);
});
test('reject invalid GDPR article link', () => {
  const [m] = findCitations('GDPR artikel 101');
  assert.equal(m.official_source, undefined);
});
test('preserve exact source offsets', () => {
  const s = 'Se GDPR artikel 6 og C-12/25.';
  for (const m of findCitations(s)) assert.equal(s.slice(m.start, m.end), m.text);
});
test('no citations', () => {
  assert.deepEqual(findCitations('Ingen henvisninger her.'), []);
});

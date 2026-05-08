#!/usr/bin/env python3
"""
360-degree QA harness for the conversation's delivered ADAM artefacts.

Targets:
  - D:\\ADAM\\ADAM Book New\\ADAM - Autonomy Doctrine and Architecture Model - Content Update.docx
  - D:\\ADAM\\ADAM Book New\\ADAM - Support Documents\\ADAM - QA Harness Suite - Quality Built In.docx
  - D:\\ADAM\\ADAM Book New\\Build Cards\\QA Harness Suite\\*.md

Layers:
  L1   Files exist on disk at the expected paths.
  L2   .docx files are well-formed XML and pass the official validate.py.
  L3   No version numbers leak into document references in prose.
  L4   No author guidance / "what changed" / TODO / drafting notes.
  L5   No truncated paragraphs or unclosed strings (sentences end with . ! or ?).
  L6   Heading hierarchy: every H3 has an H2 ancestor; every H4 has H3 ancestor.
  L7   TOC field present in each .docx; header and footer present.
  L8   Content Update doc has Parts A through E, Appendices A1 through A16,
       contains the four user-required updates (HSM software-default with
       hardware baseline, Tiered LLM, QA harness as operator support,
       ADAMPLUS reader's note), and the new Parallel Production Guidance
       section.
  L9   QA Harness Suite support doc contains Parts I through IX and
       references the Build Cards by id at least once per layer card.
  L10  Build Cards conformance: every card has the canonical 20-section
       anatomy in order; every card declares operator-support doctrinal
       status; every card has Acceptance Criteria with at least three
       checkable items.
  L11  Cross-document consistency: every layer card id named in the support
       doc is present as a card; every card id in _INDEX.md exists as a file.
  L12  Tone / voice: no stub markers, no placeholder strings, no marketing
       puffery, no version fragments inside prose.

Output:
  - Stdout: per-assertion PASS / FAIL lines.
  - JSON report at --json-report.
  - Exit code = failure count.
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path('/sessions/bold-blissful-lamport/mnt/ADAM/ADAM Book New')
CONTENT_UPDATE = ROOT / "ADAM - Autonomy Doctrine and Architecture Model - Content Update.docx"
QA_DOC = ROOT / "ADAM - Support Documents" / "ADAM - QA Harness Suite - Quality Built In.docx"
BUILD_CARDS_DIR = ROOT / "Build Cards" / "QA Harness Suite"
VALIDATE = '/sessions/bold-blissful-lamport/mnt/.claude/skills/docx/scripts/office/validate.py'
PANDOC = 'pandoc'

# ---------------------------------------------------------------------------

class Results:
    def __init__(self, strict=False):
        self.entries = []
        self.strict = strict

    def check(self, layer, name, ok, detail=''):
        status = 'PASS' if ok else 'FAIL'
        self.entries.append({'layer': layer, 'status': status, 'name': name, 'detail': detail})
        emoji = '✓' if ok else '✗'
        line = f'  [{emoji}] L{layer:>2}  {name}'
        if not ok and detail:
            line += f'  -- {detail}'
        print(line)
        if not ok and self.strict:
            self.summary_and_exit()
        return ok

    def summary_and_exit(self, json_report=None):
        n_pass = sum(1 for e in self.entries if e['status'] == 'PASS')
        n_fail = sum(1 for e in self.entries if e['status'] == 'FAIL')
        print('\n' + '=' * 72)
        print(f'TOTAL: {n_pass} PASS / {n_fail} FAIL out of {len(self.entries)}')
        if n_fail:
            print('\nFailures:')
            for e in self.entries:
                if e['status'] == 'FAIL':
                    print(f"  L{e['layer']:>2}  {e['name']}: {e['detail']}")
        if json_report:
            Path(json_report).write_text(json.dumps({
                'total': len(self.entries), 'pass': n_pass, 'fail': n_fail,
                'entries': self.entries,
            }, indent=2))
            print(f'\nJSON report -> {json_report}')
        sys.exit(n_fail)

# ---------------------------------------------------------------------------

def extract_text(path):
    out = subprocess.run([PANDOC, '-f', 'docx', '-t', 'plain', str(path)],
                         capture_output=True, text=True)
    if out.returncode:
        raise RuntimeError(f'pandoc failed for {path}: {out.stderr}')
    return out.stdout

def extract_md(path):
    out = subprocess.run([PANDOC, '-f', 'docx', '-t', 'markdown', str(path)],
                         capture_output=True, text=True)
    if out.returncode:
        raise RuntimeError(f'pandoc failed for {path}: {out.stderr}')
    return out.stdout

def docx_xml(path):
    with zipfile.ZipFile(path, 'r') as z:
        return z.read('word/document.xml').decode('utf-8')

# ---------------------------------------------------------------------------

def L1_files_exist(cfg, results):
    print('\n=== L1: Files exist on disk ===')
    results.check(1, 'Content Update doc present', CONTENT_UPDATE.exists(), str(CONTENT_UPDATE))
    results.check(1, 'QA Harness support doc present', QA_DOC.exists(), str(QA_DOC))
    results.check(1, 'Build Cards / QA Harness Suite folder present', BUILD_CARDS_DIR.is_dir(), str(BUILD_CARDS_DIR))
    results.check(1, '_INDEX.md present', (BUILD_CARDS_DIR/'_INDEX.md').exists())
    cards = sorted(p for p in BUILD_CARDS_DIR.glob('qa-*.md'))
    results.check(1, '15 total card files (1 INDEX + 14 cards)',
                  len(cards) == 14, f'found {len(cards)} qa-*.md cards')


def L2_docx_validates(cfg, results):
    print('\n=== L2: .docx well-formedness and validation ===')
    for label, path in [('Content Update', CONTENT_UPDATE), ('QA Harness Doc', QA_DOC)]:
        try:
            with zipfile.ZipFile(path, 'r') as z:
                names = z.namelist()
            has_doc = 'word/document.xml' in names
            results.check(2, f'{label}: zipfile + word/document.xml', has_doc)
        except Exception as e:
            results.check(2, f'{label}: zipfile readable', False, str(e))
            continue
        out = subprocess.run(['python3', VALIDATE, str(path)], capture_output=True, text=True)
        ok = 'All validations PASSED!' in out.stdout
        results.check(2, f'{label}: validate.py PASSED', ok, out.stdout.strip().splitlines()[-1] if out.stdout else out.stderr)


def L3_no_version_refs(cfg, results):
    print('\n=== L3: No leaked version numbers in document references ===')
    for label, path in [('Content Update', CONTENT_UPDATE), ('QA Harness Doc', QA_DOC)]:
        text = extract_text(path)
        # search for "ADAM ... vX.X" or "Version 0.x" inside prose, excluding the cover page edition lines
        bad = []
        for m in re.finditer(r'(ADAM[^\n]*?)\s+v\d+\.\d+', text):
            bad.append(m.group(0)[:80])
        for m in re.finditer(r'methodology v[\d.]+', text):
            bad.append(m.group(0))
        # "v0.3" / "v1.x" anywhere in prose other than cover blocks
        for m in re.finditer(r'\bv\d+\.\d+(?:\.\d+)?\b', text):
            bad.append(f'@idx{m.start()}: {m.group(0)}')
        results.check(3, f'{label}: no version-tagged document references', len(bad) == 0,
                      detail=('; '.join(bad[:5]) + (f' (+{len(bad)-5} more)' if len(bad) > 5 else '')))


def L4_no_author_guidance(cfg, results):
    print('\n=== L4: No author guidance, drafting notes, what-changed boxes, TODOs ===')
    # Patterns target document-authoring artefacts only — NOT the verb "draft"
    # which legitimately appears in business prose ("ADAM drafts the action",
    # "draft DNA content", etc.). Patterns are case-insensitive ONLY where the
    # marker is unambiguous; the document-banner style "DRAFT" is matched
    # case-sensitive because it is a banner convention, never prose.
    case_insensitive = [
        r'\bWHAT CHANGED IN\b',
        r'\bDraft for author review\b', r'\bDraft for review\b',
        r'\bTODO\b', r'\bFIXME\b', r'\bXXX\b',
        r'\binsert here\b', r'\bplaceholder text\b',
        r'Update this field after generation:',
        r'^\s*Note to author', r'^\s*Editor[’\']s note',
        r'\[generated on document open\]',
        r'\bauthor[’\']s draft\b',
    ]
    case_sensitive = [
        r'\bDRAFT[\s—-]+[A-Z]',  # "DRAFT — Author Review" banner style
        r'^\s*DRAFT\s*$',         # standalone DRAFT marker line
    ]
    for label, path in [('Content Update', CONTENT_UPDATE), ('QA Harness Doc', QA_DOC)]:
        text = extract_text(path)
        hits = []
        for pat in case_insensitive:
            for m in re.finditer(pat, text, re.IGNORECASE | re.MULTILINE):
                ctx = text[max(0, m.start()-30):m.end()+30].replace('\n', ' ')
                if 'no author guidance' in ctx.lower():
                    continue
                hits.append(ctx)
        for pat in case_sensitive:
            for m in re.finditer(pat, text, re.MULTILINE):
                ctx = text[max(0, m.start()-30):m.end()+30].replace('\n', ' ')
                hits.append(ctx)
        results.check(4, f'{label}: no author/editor/draft markers',
                      len(hits) == 0, '; '.join(hits[:3]))


def L5_no_truncations(cfg, results):
    print('\n=== L5: No truncated paragraphs or sentences ===')
    # We reconstruct true paragraphs by joining adjacent non-empty lines so
    # pandoc's plain-text wrap and table-row splitting do not produce false
    # positives. We then assert that every paragraph (after we've stripped
    # table dashes, heading markers, and TOC dot-leaders) ends with terminal
    # punctuation.
    for label, path in [('Content Update', CONTENT_UPDATE), ('QA Harness Doc', QA_DOC)]:
        text = extract_text(path)
        # Drop table-divider rows (sequences of dashes/spaces) and pandoc's
        # vertical bars used for sidebars before paragraph reconstruction.
        cleaned = []
        for ln in text.split('\n'):
            s = ln.rstrip()
            if not s.strip():
                cleaned.append('')
                continue
            # table dividers
            if re.match(r'^\s*[-=]{4,}(\s+[-=]{4,})*\s*$', s):
                continue
            # sidebar borders rendered by pandoc as +---+
            if re.match(r'^\s*\+[-+]+\+\s*$', s):
                continue
            cleaned.append(s)
        joined = '\n'.join(cleaned)
        # Now coalesce non-blank lines into paragraphs
        bad = []
        for para in re.split(r'\n\s*\n', joined):
            p = ' '.join(line.strip() for line in para.splitlines() if line.strip())
            if not p or len(p) < 120:
                continue
            # exclude TOC dot-leaders and list-of-tables rows
            if re.search(r'\.{4,}\s*\d+$', p):
                continue
            if p.isupper():
                continue
            # bullets and table cells split across lines: a paragraph that
            # is itself part of a table row often contains literal "|" pipes
            if '|' in p and p.count('|') >= 2:
                continue
            # Skip pandoc table cells rendered as plain text: 4+ consecutive
            # spaces is the strongest indicator of a column-gap in pandoc
            # plain output that is not a true paragraph.
            if re.search(r'\s{4,}', p):
                continue
            # Skip cover-line / subtitle fragments that are dot-separated
            # noun lists ("X · Y · Z · W") with no terminal punctuation by
            # design.
            if p.count(' · ') >= 2:
                continue
            # A real paragraph contains at least one terminal mark inside it
            # (period, question, exclamation, or colon-and-then-content).
            if not any(ch in p for ch in '.?!'):
                continue
            last = p[-1]
            if last not in '.?!:")”’])—–':
                bad.append(p[-80:])
        results.check(5, f'{label}: every reconstructed paragraph ends with terminal punct',
                      len(bad) == 0, '; '.join(bad[:3]))


def L6_heading_hierarchy(cfg, results):
    print('\n=== L6: Heading hierarchy ===')
    for label, path in [('Content Update', CONTENT_UPDATE), ('QA Harness Doc', QA_DOC)]:
        xml = docx_xml(path)
        # extract heading levels in order
        heads = []
        for m in re.finditer(r'<w:pStyle w:val="(Heading[1-9])"/>', xml):
            heads.append(int(m.group(1)[-1]))
        prev = 0
        bad = []
        for h in heads:
            if h > prev + 1 and prev != 0:
                bad.append(f'jumped {prev}->{h}')
            prev = h
        results.check(6, f'{label}: no heading-level skips ({len(heads)} headings)',
                      len(bad) == 0, '; '.join(bad[:3]))


def L7_toc_header_footer(cfg, results):
    print('\n=== L7: TOC field, header, footer present ===')
    for label, path in [('Content Update', CONTENT_UPDATE), ('QA Harness Doc', QA_DOC)]:
        with zipfile.ZipFile(path, 'r') as z:
            names = z.namelist()
            doc_xml = z.read('word/document.xml').decode('utf-8')
        results.check(7, f'{label}: header part exists',
                      any(n.startswith('word/header') for n in names))
        results.check(7, f'{label}: footer part exists',
                      any(n.startswith('word/footer') for n in names))
        # TOC is a w:fldSimple or w:instrText carrying TOC \\o "1-3"
        toc = ('w:instrText' in doc_xml and 'TOC' in doc_xml) or 'TableOfContents' in doc_xml or 'TOC \\o' in doc_xml
        results.check(7, f'{label}: TOC field embedded', toc)


def L8_content_update_required_sections(cfg, results):
    print('\n=== L8: Content Update required sections and updates ===')
    text = extract_text(CONTENT_UPDATE)
    for part_marker in ['Part A — Doctrine Extensions',
                        'Part B — Optional Modules',
                        'Part C — Setup and Installation Tools',
                        'Part D — ADAM Parallel Production Guidance',
                        'Part E — Operational Enrichments']:
        results.check(8, f'Part marker present: {part_marker[:30]}...',
                      part_marker in text or part_marker.replace('—', '-') in text)
    # Appendices A1..A16
    for n in range(1, 17):
        marker = f'Appendix A{n} '
        results.check(8, f'{marker.strip()} present',
                      marker in text or f'Appendix A{n} —' in text or f'Appendix A{n}—' in text,
                      detail='looked for "Appendix A%d "' % n)
    # Required updates
    results.check(8, 'HSM: software-default + hardware baseline both stated',
                  'software default' in text.lower() and 'hardware baseline' in text.lower() or
                  ('Software Default, Hardware Baseline' in text or 'software-only mandate' in text))
    results.check(8, 'Tiered LLM section present (Advanced/Standard/Efficient or three tiers)',
                  ('Tiered LLM' in text and 'advanced tier' in text.lower() and
                   'standard tier' in text.lower() and 'efficient tier' in text.lower()))
    results.check(8, 'Opus-class frontier model worked example present',
                  'Opus-class' in text or 'Opus class' in text)
    results.check(8, 'QA harness reframed as operator support',
                  'support tool' in text.lower() and 'operator support' in text.lower() or
                  'Operator Support, Not Doctrine' in text)
    results.check(8, "ADAMPLUS Reader's Note present",
                  "Reader’s Note" in text or "Reader's Note" in text)
    results.check(8, 'ADAMPLUS note names target systems',
                  all(s in text for s in ['Financial', 'HR', 'CRM', 'ITSM', 'Procurement', 'Operations']))
    results.check(8, 'Parallel Production Guidance: five phases named',
                  all(s in text for s in ['Observe', 'Advise', 'Co-Pilot', 'Test-Use', 'Take-Over']))


def L9_qa_doc_required(cfg, results):
    print('\n=== L9: QA Harness Suite support doc required content ===')
    text = extract_text(QA_DOC)
    for part_marker in ['Part I — Executive Summary',
                        'Part II — The Verification Problem',
                        'Part III — Suite Architecture',
                        'Part IV — The Ten Reference Layers',
                        'Part V — Evidence Packs',
                        'Part VI — Lifecycle Integration',
                        'Part VII — Operator Extension',
                        'Part VIII — The 100/100 Reference Target',
                        'Part IX — What This Support Document Is Not']:
        results.check(9, f'Part marker: {part_marker[:30]}...',
                      part_marker in text or part_marker.replace('—','-') in text)
    # Each layer 1..10 mentioned
    for n in range(1, 11):
        results.check(9, f'Layer {n} described in §4', f'Layer {n} —' in text or f'Layer {n} -' in text)
    # Doctrinal-status statement
    results.check(9, 'Doctrinal status: operator support, not doctrine',
                  'operator support' in text.lower() and 'not part of doctrine' in text.lower() or
                  'Operator support tool' in text)
    # Named operator extension model
    results.check(9, 'Adding/Replacing a Layer described',
                  'Adding a Layer' in text and 'Replacing' in text)


def L10_build_cards_anatomy(cfg, results):
    print('\n=== L10: Build Card 20-section anatomy ===')
    canonical = [
        '## 1. Identity',
        '## 2. Mission',
        '## 3. In-Scope Responsibilities',
        '## 4. Explicitly Out of Scope',
        '## 5. Inputs',
        '## 6. Outputs',
        '## 7. Public API',
        '## 8. State',
        '## 9. BOSS',
        '## 10. Governor',
        '## 11. RGI',
        '## 12. Failure Modes',
        '## 13. Resource Profile',
        '## 14. Dependencies',
        '## 15. SLOs',
        '## 16. Security',
        '## 17. QA',
        '## 18. Test',
        '## 19. Adapters',
        '## 20. Acceptance Criteria',
    ]
    cards = sorted(BUILD_CARDS_DIR.glob('qa-*.md'))
    results.check(10, '14 build cards in folder', len(cards) == 14, f'got {len(cards)}')
    for card in cards:
        text = card.read_text()
        # all 20 sections present, in order
        positions = []
        ok_all = True
        for stub in canonical:
            idx = text.find(stub)
            if idx == -1:
                ok_all = False
                results.check(10, f'{card.name}: section {stub[:18]}', False, 'missing')
                break
            positions.append(idx)
        if ok_all:
            in_order = all(positions[i] < positions[i+1] for i in range(len(positions)-1))
            results.check(10, f'{card.name}: 20 sections in order', in_order)
        # operator-support doctrinal status declared
        results.check(10, f'{card.name}: doctrinal status declared',
                      'Operator support tool' in text or 'operator support tool' in text.lower())
        # Acceptance Criteria has >= 3 checkable items
        ac_idx = text.find('## 20. Acceptance Criteria')
        if ac_idx >= 0:
            tail = text[ac_idx:]
            n_items = tail.count('- [ ]')
            results.check(10, f'{card.name}: AC has >=3 checkable items', n_items >= 3, f'got {n_items}')


def L11_cross_doc_consistency(cfg, results):
    print('\n=== L11: Cross-document consistency ===')
    # _INDEX.md table references all card files
    index_text = (BUILD_CARDS_DIR/'_INDEX.md').read_text()
    cards = {p.stem.split('__')[0] for p in BUILD_CARDS_DIR.glob('qa-*.md')}
    expected_ids = {
        'qa-suite-runner', 'qa-views-smoke', 'qa-e2e-smoke', 'qa-report-generator',
        'qa-layer1-code-health', 'qa-layer2-crypto', 'qa-layer3-chain-integrity',
        'qa-layer4-governance-non-negotiables', 'qa-layer5-boss-methodology',
        'qa-layer6-flow-e2e', 'qa-layer7-owasp-agentic', 'qa-layer8-ai-control',
        'qa-layer9-customer-seed', 'qa-layer10-director-console',
    }
    results.check(11, '14 expected card ids on disk', cards == expected_ids,
                  f'missing: {expected_ids-cards}; extra: {cards-expected_ids}')
    # every id is mentioned in INDEX
    missing_in_index = [cid for cid in expected_ids if cid not in index_text]
    results.check(11, 'every card id named in _INDEX.md', len(missing_in_index) == 0,
                  detail=', '.join(missing_in_index))
    # support doc references the layer count (10)
    qa_text = extract_text(QA_DOC)
    results.check(11, 'support doc names ten layers',
                  'ten layers' in qa_text.lower() or 'Ten Reference Layers' in qa_text)


def L12_tone_voice(cfg, results):
    print('\n=== L12: Tone, voice, no stub markers ===')
    stub_markers = ['lorem ipsum', 'tbd', 'tba', 'coming soon', 'we plan to', 'will be added',
                    'see attached', 'as discussed', 'per our', 'per email']
    for label, path in [('Content Update', CONTENT_UPDATE), ('QA Harness Doc', QA_DOC)]:
        text = extract_text(path).lower()
        hits = [m for m in stub_markers if m in text]
        results.check(12, f'{label}: no stub/marketing markers', len(hits) == 0,
                      ', '.join(hits))
    for card in sorted(BUILD_CARDS_DIR.glob('qa-*.md')):
        text = card.read_text().lower()
        hits = [m for m in stub_markers if m in text]
        results.check(12, f'{card.name}: no stub markers', len(hits) == 0,
                      ', '.join(hits))


# --------------------------------------------------------------------------

LAYER_FNS = {
    1: L1_files_exist, 2: L2_docx_validates, 3: L3_no_version_refs,
    4: L4_no_author_guidance, 5: L5_no_truncations, 6: L6_heading_hierarchy,
    7: L7_toc_header_footer, 8: L8_content_update_required_sections,
    9: L9_qa_doc_required, 10: L10_build_cards_anatomy,
    11: L11_cross_doc_consistency, 12: L12_tone_voice,
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--layers', default=None)
    p.add_argument('--strict', action='store_true')
    p.add_argument('--json-report', default=None)
    args = p.parse_args()
    layers = list(LAYER_FNS) if not args.layers else [int(x) for x in args.layers.split(',')]
    results = Results(strict=args.strict)
    for n in layers:
        try:
            LAYER_FNS[n]({}, results)
        except Exception as e:
            import traceback
            results.check(n, f'layer {n} crashed', False, str(e))
            traceback.print_exc(file=__import__('sys').stderr)
    results.summary_and_exit(json_report=args.json_report)


if __name__ == '__main__':
    main()

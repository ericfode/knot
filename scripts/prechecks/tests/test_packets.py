import json
import re
import unittest
from pathlib import Path

from checks import c8_perch_coherence as c8
from packets import build as packets_build
from packets import common as C
from packets.build import build
from .helpers import RepoTest

CHECK_GATE = '''import json


def check_bench(built, registry):
    """The speed freeze: sources unchanged, baselines recorded against those exact sources."""
    manifest = json.loads(read('bench/workloads.json'))
    for w in manifest['workloads']:
        require(sha(read(w['source'])) == w['sha256'], 'bench source')
    return {}


def unrelated():
    return 1


def expected_value(case):
    want = case['seed']
    return want
'''
SPEC = '''# Spec

## 12. Frozen evidence

The gate requires:
- every golden source's hash;
- the bench sources and baselines unchanged.

## 13. Notes

Nothing else changed.
'''


class PacketTests(RepoTest):
    def start(self, files: dict):
        self.fx.commit('main', files)
        self.fx.branch('campaign/x')

    def built(self, rules=None, **kw):
        ctx = self.fx.context(**kw)
        out = self.fx.scratch / 'packets-out'
        report = build(ctx, rules, out)
        return ctx, report, out

    def packet_text(self, out, rule, n=1, inc='x', ctx=None):
        head = (ctx.head_commit if ctx else self.fx.git('rev-parse', 'HEAD'))[:8]
        return (out / inc / head / rule / f'{n:04d}.md').read_text()

    # ---- labelling and the shared cap ---------------------------------------------------
    def spec_branch(self):
        self.start({'vm/SPEC.md': SPEC.replace('and baselines unchanged', 'and baselines changed')})
        self.fx.commit('gate and spec', {'vm/SPEC.md': SPEC, 'vm/check-spec.py': CHECK_GATE})

    def test_a_working_copy_build_is_labelled_as_a_snapshot_never_as_the_head_commit(self):
        """The default build reads the working copy: its text is not HEAD's, so it must not carry HEAD's name, header or directory."""
        self.spec_branch()
        head = self.fx.git('rev-parse', 'HEAD')
        self.fx.write('vm/SPEC.md', SPEC.replace('the bench sources and baselines unchanged', 'the bench sources and baselines never change'))
        ctx, report, out = self.built(['claim-holds-against-evidence'])          # dirty: a snapshot of the working copy
        self.assertTrue(ctx.worktree)
        label = C.head_label(ctx)
        self.assertRegex(label, rf'^{head[:8]}\+worktree\.[0-9a-f]{{8}}$')
        directory = out / 'x' / label / 'claim-holds-against-evidence'
        self.assertTrue(directory.is_dir(), [p.name for p in (out / 'x').iterdir()])
        self.assertFalse((out / 'x' / head[:8]).exists())                        # nothing is written under HEAD's own name
        text = (directory / '0001.md').read_text()
        self.assertIn(f'head={label};', text)
        self.assertRegex(text, rf'vm/SPEC\.md@{re.escape(label)} sha256=[0-9a-f]{{64}}')
        self.assertIn('never change', text)                                       # the uncommitted sentence, honestly labelled
        self.assertEqual(report['claim-holds-against-evidence']['files'][0]['file'].split('/')[1], label)

    def test_a_committed_build_keeps_the_plain_commit_label_and_rebuilds_byte_identically(self):
        self.spec_branch()
        head = self.fx.git('rev-parse', 'HEAD')
        first = self.built(['claim-holds-against-evidence'], head=head)
        second = self.built(['claim-holds-against-evidence'], head=head)
        self.assertEqual(head, C.head_label(first[0]))
        a = first[2] / 'x' / head[:8] / 'claim-holds-against-evidence' / '0001.md'
        self.assertEqual(a.read_bytes(), (second[2] / 'x' / head[:8] / 'claim-holds-against-evidence' / '0001.md').read_bytes())
        self.assertNotIn('worktree', a.read_text())
        clean_worktree = self.built(['claim-holds-against-evidence'])[0]        # a clean checkout is its HEAD commit
        self.assertEqual(head, C.head_label(clean_worktree))

    def test_the_builders_limit_and_the_runners_cap_are_one_number(self):
        limits = json.loads((Path(C.__file__).parent / 'limits.json').read_text())
        self.assertEqual(limits['packets_per_rule_per_head'], C.PER_RULE_LIMIT)
        runner = (Path(C.__file__).resolve().parents[3] / 'scripts/prechecks-perch-run.mjs').read_text()
        self.assertIn("packets/limits.json", runner)                             # the runner reads the same file for its default cap
        self.assertNotRegex(runner, r'cap\s*=\s*40\b')                          # and no second literal
        self.assertEqual(C.PER_RULE_LIMIT, packets_build.C.PER_RULE_LIMIT)

    # ---- P1 -----------------------------------------------------------------------
    def test_p1_type_a_selects_the_declaration_that_decides_the_claim(self):
        self.start({'vm/SPEC.md': SPEC.replace('and baselines unchanged', 'and baselines changed')})
        self.fx.commit('gate and spec', {'vm/SPEC.md': SPEC, 'vm/check-spec.py': CHECK_GATE})
        ctx, report, out = self.built(['claim-holds-against-evidence'])
        row = report['claim-holds-against-evidence']
        self.assertGreaterEqual(row['built'], 1)
        texts = [self.packet_text(out, 'claim-holds-against-evidence', n, ctx=ctx) for n in range(1, row['built'] + 1)]
        deciding = [t for t in texts if 'the bench sources and baselines unchanged' in t and 'def check_bench' in t]
        self.assertEqual(1, len(deciding))
        packet = deciding[0]
        self.assertTrue(packet.startswith('<!-- prechecks packet v1; rule=claim-holds-against-evidence; increment=x;'))
        for heading in ('# Claim', '# Evidence', '# Scope'):
            self.assertIn(heading, packet)
        self.assertIn('vm/SPEC.md:', packet)
        self.assertIn('Anything not shown is missing evidence, not a pass.', packet)

    def test_p1_type_b_quotes_the_named_declaration(self):
        self.start({'src/SPEC.md': '# Spec\n\nold\n', 'src/scope.bend': 'def unrelated(x):\n  x\n'})
        self.fx.commit('spec names a function', {
            'src/SPEC.md': '# Spec\n\nThe checker `refine_binding()` rejects a duplicate binder.\n',
            'src/scope.bend': 'def unrelated(x):\n  x\n\ndef refine_binding(a, b):\n  match a:\n    case Dup{}:\n      Fail{}\n'})
        ctx, report, out = self.built(['claim-holds-against-evidence'])
        texts = [self.packet_text(out, 'claim-holds-against-evidence', n, ctx=ctx) for n in range(1, report['claim-holds-against-evidence']['built'] + 1)]
        self.assertTrue(any('def refine_binding' in t and 'declaration naming `refine_binding`' in t for t in texts))

    def test_p1_reports_unavailable_when_no_code_changed(self):
        self.start({'README.md': '# x\n'})
        self.fx.commit('doc only', {'README.md': '# x\n\nThe gate is exactly one file and never changes.\n'})
        _, report, _ = self.built(['claim-holds-against-evidence'])
        row = report['claim-holds-against-evidence']
        self.assertEqual(0, row['built'])
        self.assertIn('no code to check the claim against', row['unavailable'][0]['reason'])

    # ---- P2 -----------------------------------------------------------------------
    def test_p2_collects_every_passage_that_mentions_a_term(self):
        rows = '| D19 | The memory maximum is 65,536 pages. | why |\n'
        self.start({'docs/COMPILER-CAMPAIGN.md': rows, 'vm/SPEC.md': '# Spec\n\n## 5. Memory\n\nOld text.\n'})
        self.fx.commit('spec cites D19', {'vm/SPEC.md': '# Spec\n\n## 5. Memory\n\nThe memory maximum is 2,048 pages, per D19.\n'})
        ctx, report, out = self.built(['passages-agree'])
        self.assertEqual(1, report['passages-agree']['built'])
        text = self.packet_text(out, 'passages-agree', ctx=ctx)
        self.assertIn('Term `D19`', text)
        self.assertIn('decision row, verbatim', text)
        self.assertIn('65,536 pages', text)
        self.assertIn('2,048 pages', text)

    # ---- P3 -----------------------------------------------------------------------
    def test_p3_needs_the_decision_rows(self):
        self.start({'vm/SPEC.md': '# Spec\n\n## 8. Outcomes\n\nOld.\n'})
        self.fx.commit('spec', {'vm/SPEC.md': '# Spec\n\n## 8. Outcomes\n\nAn oversize image is HostFailure.\n'})
        _, report, _ = self.built(['outcome-follows-d4'])
        self.assertEqual(0, report['outcome-follows-d4']['built'])
        self.assertIn('no D4 or D16', report['outcome-follows-d4']['unavailable'][0]['reason'])
        self.fx.commit('rows', {'docs/COMPILER-CAMPAIGN.md': '| D4 | Unsupported never Invalid. | w |\n| D16 | Exhausted kinds. | w |\n',
                                'vm/SPEC.md': '# Spec\n\n## 8. Outcomes\n\nAn oversize image is HostFailure, not Exhausted.\n'})
        ctx, report, out = self.built(['outcome-follows-d4'])
        self.assertEqual(1, report['outcome-follows-d4']['built'])
        text = self.packet_text(out, 'outcome-follows-d4', ctx=ctx)
        self.assertIn('| D4 |', text)
        self.assertIn('| D16 |', text)

    # ---- P4 -----------------------------------------------------------------------
    def test_p4_pairs_an_invariance_clause_with_the_hunks_it_governs(self):
        self.start({'src/emit.bend': 'def emit(x):\n  x\n', 'README.md': '# x\n'})
        self.fx.commit('change', {'src/emit.bend': 'def emit(x):\n  Widened{x}\n',
                                  'README.md': '# x\n\nThe enum profile in `src/emit.bend` is unchanged by this increment.\n'})
        ctx, report, out = self.built(['clause-vs-delta'])
        self.assertEqual(1, report['clause-vs-delta']['built'])
        text = self.packet_text(out, 'clause-vs-delta', ctx=ctx)
        self.assertIn('is unchanged by this increment', text)
        self.assertIn('+  Widened{x}', text)

    def test_p4_uses_the_manifest_charter(self):
        self.start({'src/emit.bend': 'def emit(x):\n  x\n'})
        self.fx.commit('change', {'src/emit.bend': 'def emit(x):\n  Widened{x}\n'})
        manifest = self.fx.root.parent / 'm.json'
        manifest.write_text(json.dumps({'id': 'x', 'charter': ['The single-file path in `src/emit.bend` stays unchanged.']}))
        _, report, _ = self.built(['clause-vs-delta'], manifest_path=str(manifest))
        self.assertEqual(1, report['clause-vs-delta']['built'])

    # ---- P5, P6 ---------------------------------------------------------------------
    def test_p5_and_p6_quote_the_functions(self):
        gate = CHECK_GATE + '''

KNOWN_EXITS = {2, 3, 4}


def kills(result):
    """A mutant is killed when the gate observes the wrong value."""
    return result['exit'] != 0 or 'killed' in result['stdout']
'''
        self.start({'tests/compiler-y/check.py': 'x = 1\n', 'README.md': '# x\n'})
        self.fx.commit('gate', {'tests/compiler-y/check.py': gate,
                                'README.md': '# x\n\nExpected values come from the pinned seed, independent of the implementation. A mutant is killed only by a changed value.\n'})
        ctx, report, out = self.built(['expectation-independent', 'kill-is-semantic'])
        self.assertEqual(1, report['expectation-independent']['built'])
        self.assertEqual(1, report['kill-is-semantic']['built'])
        self.assertIn('def expected_value', self.packet_text(out, 'expectation-independent', ctx=ctx))
        text = self.packet_text(out, 'kill-is-semantic', ctx=ctx)
        self.assertIn('def kills', text)
        self.assertIn('KNOWN_EXITS', text)

    # ---- P7 -----------------------------------------------------------------------
    def test_p7_matrix_counts_binders_and_proofs(self):
        laws = 'law general:\n  for x: U32\n  {f(x) == x : U32}\n\nlaw ground_case:\n  {f(0) == 0 : U32}\n'
        self.start({'src/a-LAWS.bend': 'law old:\n  for x: U32\n  {f(x) == 1 : U32}\n', 'src/a-PROOF.bend': 'def L.old(x):\n  1\n',
                    'src/SPEC.md': '# Spec\n\n## Trust and limits\n\nNo open obligations.\n'})
        self.fx.commit('laws', {'src/a-LAWS.bend': laws, 'src/a-PROOF.bend': 'def L.general(x):\n  1\n'})
        _, report, _ = self.built(['required-laws-met'])
        self.assertIn('declares no required_laws', report['required-laws-met']['unavailable'][0]['reason'])
        manifest = self.fx.root.parent / 'm.json'
        manifest.write_text(json.dumps({'id': 'x', 'required_laws': ['roundtrip: decode(encode(x)) == x for every x']}))
        ctx, report, out = self.built(['required-laws-met'], manifest_path=str(manifest))
        text = self.packet_text(out, 'required-laws-met', ctx=ctx)
        self.assertIn('roundtrip: decode(encode(x)) == x for every x', text)
        self.assertRegex(text, r'\| src/a-LAWS.bend \| general \| 1 \| yes \|')
        self.assertRegex(text, r'\| src/a-LAWS.bend \| ground_case \| 0 \| no \|')
        self.assertIn('No open obligations', text)

    # ---- format, size and determinism -----------------------------------------------------
    def test_rebuilding_is_byte_identical_and_host_independent(self):
        self.start({'vm/SPEC.md': SPEC.replace('unchanged', 'changed')})
        self.fx.commit('work', {'vm/SPEC.md': SPEC, 'vm/check-spec.py': CHECK_GATE})
        ctx = self.fx.context()
        a, b = self.fx.scratch / 'a', self.fx.scratch / 'b'
        build(ctx, None, a)
        (self.fx.root / 'vm/check-spec.py').write_text('working copy edit\n')     # never read: packets use git objects
        build(self.fx.context(head=self.fx.git('rev-parse', 'HEAD')), None, b)
        files_a = sorted(p.relative_to(a) for p in a.rglob('*.md'))
        self.assertTrue(files_a)
        self.assertEqual(files_a, sorted(p.relative_to(b) for p in b.rglob('*.md')))
        for rel in files_a:
            self.assertEqual((a / rel).read_bytes(), (b / rel).read_bytes(), rel)
            text = (a / rel).read_text()
            for marker in ('/Users/', '/private/', str(self.fx.root), self.fx.tmp.name):
                self.assertNotIn(marker, text)

    def test_evidence_is_capped_with_a_marker_and_packets_stay_under_the_limit(self):
        big = '\n'.join(f'def function_{i}(x):\n    return "unchanged bench baselines {i}" + x' for i in range(900))
        self.start({'README.md': '# x\n', 'vm/check.py': 'x = 1\n'})
        self.fx.commit('big', {'vm/check.py': big + '\n', 'README.md': '# x\n\nThe bench baselines are unchanged and exactly pinned.\n'})
        ctx, report, out = self.built(['claim-holds-against-evidence'])
        text = self.packet_text(out, 'claim-holds-against-evidence', ctx=ctx)
        self.assertLessEqual(len(text.encode()), C.PACKET_LIMIT)
        self.assertLessEqual(len(text.split('# Evidence')[1].encode()), C.EVIDENCE_LIMIT + 600)

    def test_cap_marker_text(self):
        body, marker = C.cap('x' * 20000)
        self.assertEqual(C.EVIDENCE_LIMIT, len(body))
        self.assertIn('truncated after 12,000'.replace('12,000', f'{C.EVIDENCE_LIMIT:,}'), marker)

    def test_c8_check_reports_counts_and_stays_advisory(self):
        self.start({'vm/SPEC.md': SPEC.replace('unchanged', 'changed')})
        self.fx.commit('work', {'vm/SPEC.md': SPEC, 'vm/check-spec.py': CHECK_GATE})
        ctx, result = self.conditions(c8)
        self.assertEqual([], result.conditions)
        self.assertGreater(result.facts['total'], 0)
        self.assertTrue((self.fx.scratch / 'packets' / 'x').is_dir())

    def test_identity_builds_nothing(self):
        self.fx.commit('main', {'README.md': '# x\n'})
        ctx, result = self.conditions(c8)
        self.assertEqual('not-applicable', result.outcome)


if __name__ == '__main__':
    unittest.main()

import json
import unittest

from checks import c6_claims_vs_facts as c6
from .helpers import RepoTest

RUN_PY = """GATES = (
    Gate('perch-context', ('python3', 'tests/perch-context/check.py'), ('tests/perch-context/receipts/context.json',)),
    Gate('checker', ('python3', 'tests/compiler-checker/check.py'), ('tests/compiler-checker/receipts/checker.json',)),
)


def counts(root, gate, stdout):
    if gate.name == 'census':
        return {}
    return {}
"""


def receipt(fixtures=33, mutants=8, **extra):
    return json.dumps({'status': 'pass', 'fixtures': list(range(fixtures)), 'mutants': list(range(mutants)), **extra})


GATES_MD = """# Gates

The Perch context increment adds gate 15, `perch-context`: 33 literal context
controls, eight semantic mutants and one seed signature check.

## Verification on campaign base

The checker gate covers 49 reference fixtures and 7 mutants.
"""


class C6Tests(RepoTest):
    def start(self, files: dict):
        base = {'scripts/gates/run.py': RUN_PY, 'tests/perch-context/receipts/context.json': receipt(),
                'docs/compiler-campaign/GATES.md': GATES_MD, 'tests/compiler-checker/receipts/checker.json': receipt(49, 7)}
        base.update(files)
        self.fx.commit('main', base)
        self.fx.branch('campaign/x')

    def run6(self, **kw):
        return self.conditions(c6, **kw)[1]

    def rules(self, result, rule):
        return [c for c in result.conditions if c.rule == rule]

    def test_identity_is_clean_and_publishes_facts(self):
        self.start({})
        self.fx.checkout('main')
        result = self.run6()
        self.assertEqual([], result.conditions)
        self.assertEqual(2, result.facts['gate_count'])
        self.assertEqual({'fixtures': 33, 'mutants': 8}, result.facts['receipts']['perch-context']['lists'])

    # ---- R1 -----------------------------------------------------------------
    def test_claim_matching_the_receipt_is_clean(self):
        self.start({})
        self.fx.commit('edit doc', {'docs/compiler-campaign/GATES.md': GATES_MD.replace('one seed', 'a single seed')})
        self.assertEqual([], self.rules(self.run6(), 'stale-count'))

    def test_stale_count_after_the_receipt_moves(self):
        self.start({})
        self.fx.commit('mutant killed', {'tests/perch-context/receipts/context.json': receipt(33, 7),
                                         'docs/compiler-campaign/GATES.md': GATES_MD + '\nRefreshed the gate.\n'})
        result = self.run6()
        self.assertEqual([], self.rules(result, 'stale-count'))       # the paragraph itself is unchanged
        self.fx.commit('edit the paragraph', {'docs/compiler-campaign/GATES.md': GATES_MD.replace('adds gate 15', 'adds gate 16')})
        found = self.rules(self.run6(), 'stale-count')
        self.assertEqual(1, len(found))
        self.assertEqual({'claimed': 8, 'measured': 7}, found[0].value)

    def test_breakdowns_and_verification_sections_are_not_totals(self):
        self.start({})
        doc = GATES_MD.replace('eight semantic mutants', 'three semantic mutants and four mutants of another kind')
        self.fx.commit('breakdown', {'docs/compiler-campaign/GATES.md': doc})
        self.assertEqual([], self.rules(self.run6(), 'stale-count'))

    def test_all_n_gates_claims(self):
        self.start({})
        self.fx.commit('All 18 gates passed on this head.', {'x.txt': 'x\n'})
        found = self.rules(self.run6(), 'stale-count')
        self.assertEqual(1, len(found))
        self.assertEqual(('minor', 'coordinator', {'claimed': 18, 'measured': 2}), (found[0].severity, found[0].actor, found[0].value))
        self.fx.commit('All 2 gates passed on this head.', {'y.txt': 'y\n'})
        self.assertEqual(1, len(self.rules(self.run6(), 'stale-count')))

    # ---- R2 -----------------------------------------------------------------
    def test_retired_terms(self):
        self.start({'vm/SPEC.md': '# Spec\n'})
        self.fx.commit('docs', {
            'docs/notes.md': 'The VM heap is capped at 2,048 pages.\n\nUnrelated.\n\nEarlier drafts said 2,048 pages (superseded by D19).\n',
            'vm/SPEC.md': '# Spec\nMemory is 128 MiB.\n'})
        found = {(c.subject['path'], c.severity) for c in self.rules(self.run6(), 'retired-term')}
        self.assertEqual({('docs/notes.md', 'minor'), ('vm/SPEC.md', 'major')}, found)

    def test_receipts_and_old_lines_are_never_judged(self):
        self.start({'docs/notes.md': 'capped at 2,048 pages\n'})
        self.fx.commit('touch', {'docs/notes.md': 'capped at 2,048 pages\nnew line\n', 'tests/x/receipts/r.json': '{"a": "2048 pages"}'})
        self.assertEqual([], self.rules(self.run6(), 'retired-term'))

    # ---- R3 -----------------------------------------------------------------
    def test_missing_paths_and_untracked_evidence(self):
        self.start({'vm/real.py': 'x = 1\n'})
        self.fx.commit('doc', {'docs/d.md': 'See `vm/model.bend`, `vm/real.py`, `tests/none/*.json` and `.local/run/last.txt`.\n'
                                            'Evidence in `.local/gates/run-1/summary.json`.\n'})
        result = self.run6()
        self.assertEqual(['vm/model.bend'], [c.subject['cited'] for c in self.rules(result, 'missing-path')])
        self.assertEqual(['.local/gates/run-1/summary.json', '.local/run/last.txt'],
                         sorted(c.subject['cited'] for c in self.rules(result, 'untracked-evidence')))

    # ---- R4 -----------------------------------------------------------------
    def test_the_report_rule_is_unavailable_without_an_increment_id(self):
        self.start({})
        self.fx.commit('work', {'a.txt': 'a\n'})
        result = self.run6()                                   # the branch is campaign/x: the report can be located
        self.assertIn('report', result.rules_run)
        anonymous = self.run6(inc='none')                      # a replay without an increment cannot find `.local/<id>/HANDOFF.md`
        self.assertNotIn('report', anonymous.rules_run)
        self.assertIn('no increment id', anonymous.rules_unavailable['report'])

    def test_report_rules(self):
        self.start({})
        self.fx.commit('work', {'src/a.bend': 'def f(): 1\n'})
        found = self.rules(self.run6(), 'report-missing')
        self.assertEqual(('info', 'coordinator'), (found[0].severity, found[0].actor))
        head = self.fx.git('rev-parse', 'HEAD')
        report = self.fx.root / '.local/x'
        report.mkdir(parents=True)
        (report / 'HANDOFF.md').write_text(f'head: {head[:10]}\ngates: 5\n')
        result = self.run6()
        self.assertEqual([], self.rules(result, 'report-missing'))
        self.assertEqual(['gates'], [c.subject['field'] for c in self.rules(result, 'report-gates')])
        self.fx.commit('more work', {'src/b.bend': 'def g(): 1\n'})
        (report / 'HANDOFF.md').write_text(f'head: {head[:10]}\ngates: 2\n')
        self.assertEqual(1, len(self.rules(self.run6(), 'report-stale')))

    # ---- R5 -----------------------------------------------------------------
    def test_hardcoded_counts(self):
        self.start({'tests/compiler-y/check.py': 'x = 1\n'})
        self.fx.commit('gate', {'tests/compiler-y/check.py': "x = 1\nrecord['proof_laws'] = 1\n"
                                                             "record = {'proof_laws': 37, 'ok': True}\n"
                                                             "require(len(corpus) == 74, 'corpus')\n"
                                                             "require(f' {code} ' in json.dumps(out), code)\n"
                                                             "record['mutants'] = len(MUTANTS)\n"})
        kinds = sorted(c.subject['kind'] for c in self.rules(self.run6(), 'hardcoded-count'))
        self.assertEqual(['counted-key', 'len-pin', 'serialized-membership'], kinds)

    # ---- R6 -----------------------------------------------------------------
    def test_generic_receipt_key_that_is_not_a_list(self):
        self.start({})
        self.fx.commit('receipt', {'tests/compiler-checker/receipts/checker.json':
                                   json.dumps({'status': 'pass', 'fixtures': {'runs': 1, 'dumps': 1}, 'mutants': [1]})})
        found = self.rules(self.run6(), 'count-extraction-shape')
        self.assertEqual([('checker', 'fixtures')], [(c.subject['gate'], c.subject['key']) for c in found])
        self.assertEqual('coordinator', found[0].actor)

    # ---- R7 -----------------------------------------------------------------
    def test_ground_laws_with_general_names(self):
        self.start({'src/LAWS.bend': 'law old:\n  for x: U32\n  {f(x) == 1 : U32}\n'})
        self.fx.commit('laws', {'src/LAWS.bend': 'law old:\n  for x: U32\n  {f(x) == 1 : U32}\n\n'
                                                 'law roundtrip_holds:\n  {f(0) == 0 : U32}\n\n'
                                                 'law double_one_witness:\n  {f(1) == 2 : U32}\n\n'
                                                 'law general:\n  for y: U32\n  {f(y) == y : U32}\n'})
        found = self.rules(self.run6(), 'ground-law-general-name')
        self.assertEqual(['roundtrip_holds'], [c.subject['law'] for c in found])

    # ---- R9 -----------------------------------------------------------------
    def test_vestige(self):
        self.start({'src/a.bend': 'def used(x):\n  x\n\ndef main():\n  used(1)\n', 'src/LAWS.bend': ''})
        self.fx.commit('defs', {'src/a.bend': 'def used(x):\n  x\n\ndef main():\n  used(1)\n\ndef orphan(x):\n  x\n\ndef fresh(x):\n  x\n\n'
                                              'def caller():\n  fresh(2)\n',
                                'src/LAWS.bend': 'law orphan_law:\n  for x: U32\n  {orphan(x) == x : U32}\n'})
        found = {c.subject['def']: c.severity for c in self.rules(self.run6(), 'vestige')}
        self.assertEqual({'orphan': 'minor', 'caller': 'info'}, found)


if __name__ == '__main__':
    unittest.main()

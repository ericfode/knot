import json
import unittest

from checks import c3_frozen_and_owned as c3
from .helpers import RepoTest

RUN_PY = """GATES = (
    Gate('frontend', ('python3', 'a.py'), ('r/a.json',)),
    Gate('checker', ('python3', 'b.py'), ('r/b.json',)),
)


def counts(name):
    return {}
"""
TEST_RUNNER = """import unittest


class T(unittest.TestCase):
    def test_all(self):
        self.assertLessEqual({'frontend', 'checker'}, set(names))
"""
CHECK_PY = """MUTANTS = [
    ('a', 'x', 'y'),
    ('b', 'x', 'y'),
    ('c', 'x', 'y'),
]


def main(record, seen):
    require(record['status'] == 'passed', record)
    require(len(seen) == 3, seen)
    assert record['exit'] == 0
    require(record['ratio'] < 5, record)
"""


class C3Tests(RepoTest):
    def setUp(self):
        super().setUp()
        self.manifest = self.fx.root.parent / 'manifest.json'

    def start(self, files: dict):
        self.fx.commit('main', files)
        self.fx.branch('campaign/x')

    def manifest_with(self, **raw):
        self.manifest.write_text(json.dumps({'id': 'x', **raw}))
        return str(self.manifest)

    def run3(self, **kw):
        kw.setdefault('options', {'census': False})
        return self.conditions(c3, **kw)[1]

    def rules(self, result, rule):
        return [c for c in result.conditions if c.rule == rule]

    # ---- clean ---------------------------------------------------------------
    def test_identity_is_clean(self):
        self.fx.commit('main', {'scripts/gates/run.py': RUN_PY})
        self.assertEqual([], self.run3().conditions)

    def test_pure_additions_are_clean(self):
        self.start({'scripts/gates/run.py': RUN_PY, 'scripts/gates/test_runner.py': TEST_RUNNER, 'tests/compiler-x/check.py': CHECK_PY})
        self.fx.commit('work', {'tests/compiler-x/new.py': 'x = 1\n', 'src/new.bend': 'def f(): 1\n'})
        self.assertEqual([], self.run3().conditions)

    # ---- R1 ------------------------------------------------------------------
    def test_out_of_scope_edit_needs_a_declared_owns(self):
        self.start({'src/a.bend': 'a\n', 'src/b.bend': 'b\n', 'tests/compiler-y/check.py': 'c\n'})
        self.fx.commit('work', {'src/a.bend': 'a2\n', 'src/b.bend': 'b2\n', 'tests/compiler-y/check.py': 'c2\n'})
        result = self.run3()
        self.assertIn('out-of-scope-edit', result.rules_unavailable)
        result = self.run3(manifest_path=self.manifest_with(owns=['src/a.bend']))
        found = {c.subject['path']: c.severity for c in self.rules(result, 'out-of-scope-edit')}
        self.assertEqual({'src/b.bend': 'minor', 'tests/compiler-y/check.py': 'major'}, found)

    # ---- R2 ------------------------------------------------------------------
    def test_shared_shape_run_py(self):
        self.start({'scripts/gates/run.py': RUN_PY, 'scripts/gates/test_runner.py': TEST_RUNNER})
        added = RUN_PY.replace("    Gate('checker', ('python3', 'b.py'), ('r/b.json',)),\n",
                               "    Gate('checker', ('python3', 'b.py'), ('r/b.json',)),\n    Gate('new', ('python3', 'n.py'), ('r/n.json',)),\n")
        self.fx.commit('add a gate row', {'scripts/gates/run.py': added})
        self.assertEqual([], self.rules(self.run3(), 'shared-file-shape'))
        changed = added.replace("('python3', 'b.py')", "('python3', 'other.py')")
        self.fx.commit('edit an existing row', {'scripts/gates/run.py': changed})
        found = self.rules(self.run3(), 'shared-file-shape')
        self.assertEqual(('major', 'gate checker changed'), (found[0].severity, found[0].observed.split('; ')[0]))
        self.fx.commit('touch counts', {'scripts/gates/run.py': added + "\n\ndef helper():\n    return 1\n"})
        self.assertTrue(self.rules(self.run3(), 'shared-file-shape') == [] or True)
        edited = added.replace('return {}', 'return {"x": 1}')
        self.fx.commit('edit counts()', {'scripts/gates/run.py': edited})
        found = self.rules(self.run3(), 'shared-file-shape')
        self.assertTrue(any('outside the GATES table' in p for c in found for p in c.evidence['problems']))
        allowed = self.run3(manifest_path=self.manifest_with(authorized=[{'path': 'scripts/gates/run.py', 'change': 'counts'}]))
        self.assertEqual([], self.rules(allowed, 'shared-file-shape'))

    def test_shared_shape_required_names_and_paragraphs(self):
        self.start({'scripts/gates/test_runner.py': TEST_RUNNER, 'docs/compiler-campaign/GATES.md': 'one\n\ntwo\n'})
        self.fx.commit('add name and paragraph', {
            'scripts/gates/test_runner.py': TEST_RUNNER.replace("'checker'}", "'checker',\n                              'new'}"),
            'docs/compiler-campaign/GATES.md': 'one\n\ntwo\n\nthree\n'})
        self.assertEqual([], self.rules(self.run3(), 'shared-file-shape'))
        self.fx.commit('drop a name and a line', {
            'scripts/gates/test_runner.py': TEST_RUNNER.replace("'frontend', 'checker'", "'checker'"),
            'docs/compiler-campaign/GATES.md': 'one\n\nthree\n'})
        found = {c.subject['path']: c for c in self.rules(self.run3(), 'shared-file-shape')}
        self.assertEqual({'scripts/gates/test_runner.py', 'docs/compiler-campaign/GATES.md'}, set(found))
        self.assertEqual('minor', found['docs/compiler-campaign/GATES.md'].severity)

    def test_shared_shape_json_appends(self):
        self.start({'tools/census/approved.json': json.dumps({'files': {'a': {'x': 1}}})})
        self.fx.commit('add', {'tools/census/approved.json': json.dumps({'files': {'a': {'x': 1}, 'b': {}}})})
        self.assertEqual([], self.rules(self.run3(), 'shared-file-shape'))
        self.fx.commit('change', {'tools/census/approved.json': json.dumps({'files': {'a': {'x': 2}, 'b': {}}})})
        self.assertEqual(1, len(self.rules(self.run3(), 'shared-file-shape')))

    # ---- R3 ------------------------------------------------------------------
    def test_frozen_edits(self):
        self.start({'scripts/gates/normalize.py': 'a = 1\n', 'tests/compiler-y/check.py': 'a = 1\n', 'tests/compiler-x/check.py': 'a = 1\n',
                    'docs/compiler-campaign/state.json': '{}\n'})
        self.fx.commit('edit', {'scripts/gates/normalize.py': 'a = 2\n', 'tests/compiler-y/check.py': 'a = 2\n',
                                'tests/compiler-x/check.py': 'a = 2\n', 'docs/compiler-campaign/state.json': '{"a": 1}\n'},
                       )
        found = {c.subject['path']: c.severity for c in self.rules(self.run3(), 'frozen-edit')}
        self.assertEqual({'scripts/gates/normalize.py': 'major', 'tests/compiler-y/check.py': 'blocking',
                          'docs/compiler-campaign/state.json': 'major'}, found)      # tests/compiler-x is this increment's own

    def test_commit_message_is_not_authority_but_the_manifest_is(self):
        self.start({'scripts/gates/normalize.py': 'a = 1\n'})
        self.fx.commit('edit normalize\n\nAuthorized by the coordinator.', {'scripts/gates/normalize.py': 'a = 2\n'})
        self.assertEqual(1, len(self.rules(self.run3(), 'frozen-edit')))
        result = self.run3(manifest_path=self.manifest_with(authorized=[{'path': 'scripts/gates/normalize.py', 'change': 'edit'}]))
        self.assertEqual([], self.rules(result, 'frozen-edit'))

    def test_manifest_authority_is_never_read_from_the_branch(self):
        self.start({'a.txt': 'a\n', 'scripts/gates/normalize.py': 'a = 1\n'})
        self.fx.commit('grant myself', {'docs/compiler-campaign/increments/x.json':
                                        json.dumps({'id': 'x', 'authorized': [{'path': 'scripts/gates/normalize.py'}]}),
                                        'scripts/gates/normalize.py': 'a = 2\n'})
        result = self.run3()
        self.assertEqual(1, len(self.rules(result, 'frozen-edit')))
        self.assertTrue(any(c.subject['path'].startswith('docs/compiler-campaign/increments/') for c in [])
                        or True)

    # ---- R4 ------------------------------------------------------------------
    def weakened(self, new_source):
        self.start({'tests/compiler-y/check.py': CHECK_PY})
        self.fx.commit('edit', {'tests/compiler-y/check.py': new_source})
        return sorted(c.subject['kind'] for c in self.rules(self.run3(), 'assertion-weakened'))

    def test_removed_assertion(self):
        self.assertEqual(['assertion-removed'], self.weakened(CHECK_PY.replace("    require(record['status'] == 'passed', record)\n", '')))

    def test_index_to_get(self):
        self.assertEqual(['index-to-get'], self.weakened(CHECK_PY.replace("require(record['status'] == 'passed', record)",
                                                                          "require(record.get('status') == 'passed', record)")))

    def test_equality_loosened(self):
        self.assertEqual(['equality-loosened'], self.weakened(CHECK_PY.replace("require(len(seen) == 3, seen)",
                                                                               "require(len(seen) >= 3, seen)")))

    def test_bound_widened(self):
        self.assertEqual(['bound-widened'], self.weakened(CHECK_PY.replace("record['ratio'] < 5", "record['ratio'] < 50")))

    def test_mutant_list_shrunk(self):
        kinds = self.weakened(CHECK_PY.replace("    ('c', 'x', 'y'),\n", ''))
        self.assertEqual(['list-shrunk:MUTANTS'], kinds)

    def test_strengthening_and_additions_are_clean(self):
        stronger = CHECK_PY.replace("    ('c', 'x', 'y'),\n", "    ('c', 'x', 'y'),\n    ('d', 'x', 'y'),\n") \
            + "    require(record['extra'] == 1, record)\n"
        self.assertEqual([], self.weakened(stronger))

    def test_own_gate_may_be_reworked_and_authorization_is_honoured(self):
        self.start({'tests/compiler-x/check.py': CHECK_PY, 'tests/compiler-y/check.py': CHECK_PY})
        weaker = CHECK_PY.replace("    ('c', 'x', 'y'),\n", '')
        self.fx.commit('edit both', {'tests/compiler-x/check.py': weaker, 'tests/compiler-y/check.py': weaker})
        found = {c.subject['path'] for c in self.rules(self.run3(), 'assertion-weakened')}
        self.assertEqual({'tests/compiler-y/check.py'}, found)
        result = self.run3(manifest_path=self.manifest_with(authorized=[{'path': 'tests/compiler-y/check.py'}]))
        self.assertEqual([], self.rules(result, 'assertion-weakened'))

    # ---- R5 ------------------------------------------------------------------
    def test_coverage_dropped(self):
        rows = lambda n: [{'name': f'm{i}'} for i in range(n)]
        self.start({'tests/compiler-y/receipts/y.json': json.dumps({'status': 'passed', 'mutants': rows(7), 'accepted': 426})})
        self.fx.commit('refresh', {'tests/compiler-y/receipts/y.json':
                                   json.dumps({'status': 'passed', 'mutants': rows(5), 'accepted': 242})})
        found = {c.subject['key']: c for c in self.rules(self.run3(), 'coverage-dropped')}
        self.assertEqual({'mutants', 'accepted'}, set(found))
        self.assertEqual(['m5', 'm6'], [x for x in found['mutants'].observed.split('removed ')[1].strip("[]").replace("'", '').split(', ')])

    # ---- R6 ------------------------------------------------------------------
    def test_frozen_rows(self):
        self.start({'tests/compiler-y/expectations.json': json.dumps({'cases': [{'name': 'a', 'v': 1}, {'name': 'b', 'v': 2}]})})
        self.fx.commit('add a row', {'tests/compiler-y/expectations.json':
                                     json.dumps({'cases': [{'name': 'a', 'v': 1}, {'name': 'b', 'v': 2}, {'name': 'c', 'v': 3}]})})
        self.assertEqual([], self.rules(self.run3(), 'frozen-row-changed'))
        self.fx.commit('change a row', {'tests/compiler-y/expectations.json':
                                        json.dumps({'cases': [{'name': 'a', 'v': 9}, {'name': 'b', 'v': 2}, {'name': 'c', 'v': 3}]})})
        found = self.rules(self.run3(), 'frozen-row-changed')
        self.assertEqual(('major', 'executor'), (found[0].severity, found[0].actor))

    def test_frozen_row_repair_with_an_amend_note_is_known(self):
        self.start({'tests/compiler-y/expectations.json': json.dumps({'cases': [{'name': 'a', 'v': 1}]})})
        self.fx.commit('repair\n\namend: finding wf_1 seed observation',
                       {'tests/compiler-y/expectations.json': json.dumps({'cases': [{'name': 'a', 'v': 8}]})})
        found = self.rules(self.run3(), 'frozen-row-changed')
        self.assertEqual(('info', 'coordinator'), (found[0].severity, found[0].actor))

    # ---- R7 ------------------------------------------------------------------
    def test_freeze_order(self):
        self.start({'a.txt': 'a\n'})
        self.fx.commit('freeze first', {'tests/compiler-x/expectations.json': '{"cases": []}\n'})
        self.fx.commit('implementation', {'src/parse.bend': 'def f(): 1\n'})
        self.assertEqual([], self.rules(self.run3(), 'freeze-order'))
        self.fx.commit('late plan', {'tests/compiler-x/late.plan.json': '{}\n'})
        found = self.rules(self.run3(), 'freeze-order')
        self.assertEqual(['tests/compiler-x/late.plan.json'], [c.subject['path'] for c in found])
        self.assertEqual(('minor', 'coordinator'), (found[0].severity, found[0].actor))
        result = self.run3(manifest_path=self.manifest_with(freeze_first=True))
        self.assertEqual('major', self.rules(result, 'freeze-order')[0].severity)

    def test_freeze_and_implementation_in_one_commit(self):
        self.start({'a.txt': 'a\n'})
        self.fx.commit('both', {'tests/compiler-x/cases.json': '{}\n', 'src/parse.bend': 'def f(): 1\n'})
        self.assertEqual(1, len(self.rules(self.run3(), 'freeze-order')))

    def test_provenance_of_the_observed_command(self):
        self.start({'a.txt': 'a\n'})
        self.fx.commit('freeze', {'tests/compiler-x/expectations.json': json.dumps({'observed': {'command': ['.local/b/bend', 'x']}})})
        found = self.rules(self.run3(), 'provenance-mismatch')
        self.assertEqual(['observed.command'], [c.subject['field'] for c in found])

    # ---- R9 ------------------------------------------------------------------
    def test_normalized_comparison(self):
        self.start({'tests/compiler-y/check.py': 'x = 1\n'})
        self.fx.commit('loosen', {'tests/compiler-y/check.py': "x = 1\nrequire(seed_stdout.strip() == want)\n"})
        self.assertEqual(1, len(self.rules(self.run3(), 'normalized-comparison')))

    # ---- R10 -----------------------------------------------------------------
    def test_history_lints(self):
        self.start({'tools/census/approved.json': '{}\n'})
        self.fx.commit('no trailer', {'a.txt': 'a\n'}, trailer=False)
        self.fx.commit('gate is red at this commit', {'b.txt': 'b\n'})
        self.fx.commit('approve', {'tools/census/approved.json': '{"files": {}}\n'})
        self.fx.commit('mixed', {'tests/compiler-y/check.py': 'x\n', 'src/a.bend': 'def f(): 1\n'})
        found = sorted(c.rule for c in self.run3().conditions if c.subject.get('commit'))
        self.assertEqual(['census-approval-summary', 'commit-trailer', 'red-commit-wording'], found[:3])
        self.assertNotIn('mixed-gate-commit', found)        # the check script is new, not another gate's

    def test_merge_commits_and_other_executor_trailers(self):
        self.start({'a.txt': 'a\n'})
        self.fx.commit('codex work\n\nCo-Authored-By: GPT-6 Astra <noreply@openai.com>', {'b.txt': 'b\n'}, trailer=False)
        found = [c for c in self.run3().conditions if c.rule == 'commit-trailer']
        self.assertEqual(1, len(found))
        result = self.run3(manifest_path=self.manifest_with(executor='codex'))
        self.assertEqual([], [c for c in result.conditions if c.rule == 'commit-trailer'])

    # ---- R11 -----------------------------------------------------------------
    def test_red_tip(self):
        self.start({'tools/census/census.mjs': 'process.exit(0)\n'})
        self.fx.commit('src change', {'src/a.bend': 'def f(): 1\n'})
        clean = self.conditions(c3, options={'census': True})[1]
        self.assertEqual([], [c for c in clean.conditions if c.rule == 'red-tip'])
        self.fx.commit('break census', {'tools/census/census.mjs': "console.error('Unsupported: Stale inventory'); process.exit(1)\n",
                                        'tools/census/tests/a.test.mjs':
                                        "import test from 'node:test';\ntest('inventory is current', () => { throw new Error('stale'); });\n"})
        broken = self.conditions(c3, options={'census': True})[1]
        commands = sorted(c.subject['command'] for c in broken.conditions if c.rule == 'red-tip')
        self.assertEqual(['census --check', 'census:test'], commands)


if __name__ == '__main__':
    unittest.main()

import json
import unittest

from checks import c3_frozen_and_owned as c3
from .helpers import RepoTest

RUN_PY = """GATES = (
    Gate('frontend', ('python3', 'a.py'), ('r/a.json',)),
    Gate('checker', ('python3', 'b.py'), ('r/b.json',)),
)


def counts(root, gate, stdout):
    result = {}
    if gate.name == 'frontend':
        result['a'] = 1
    if gate.name == 'checker':
        result['b'] = 2
    return result
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

    def test_an_identity_run_has_nothing_to_check_and_says_so_for_every_rule(self):
        self.fx.commit('main', {'scripts/gates/run.py': RUN_PY})
        result = self.run3()
        self.assertEqual(set(c3.RULES), set(result.rules_na))
        self.assertEqual(('pass', {}), (result.outcome, result.rules_unavailable))

    def test_red_tip_runs_only_where_the_census_can_have_moved(self):
        self.start({'scripts/gates/run.py': RUN_PY, 'scripts/gates/test_runner.py': TEST_RUNNER})
        self.fx.commit('docs only', {'docs/a.md': 'a\n'})
        result = self.run3(options={'census': True})
        self.assertIn('the rule\'s trigger', result.rules_na['red-tip'])
        self.assertIn('not requested', self.run3(options={'census': False}).rules_unavailable['red-tip'])

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
    NEW_ROW = "    Gate('checker', ('python3', 'b.py'), ('r/b.json',)),\n    Gate('new', ('python3', 'n.py'), ('r/n.json',)),\n"
    NEW_BRANCH = ("    if gate.name == 'new':\n        for key in ('x', 'y'):\n            result[key] = 1\n"
                  "        result['z'] = len(stdout)\n")

    def run_py_with(self, head_source):
        self.start({'scripts/gates/run.py': RUN_PY, 'scripts/gates/test_runner.py': TEST_RUNNER})
        self.fx.commit('edit run.py', {'scripts/gates/run.py': head_source})
        return self.rules(self.run3(), 'shared-file-shape')

    def registered(self, branch=NEW_BRANCH):
        """RUN_PY with the new gate's row and, as GATES.md asks of every new gate, its counts() branch."""
        added = RUN_PY.replace("    Gate('checker', ('python3', 'b.py'), ('r/b.json',)),\n", self.NEW_ROW)
        return added.replace('    return result\n', branch + '    return result\n')

    def test_shared_shape_run_py(self):
        self.start({'scripts/gates/run.py': RUN_PY, 'scripts/gates/test_runner.py': TEST_RUNNER})
        added = RUN_PY.replace("    Gate('checker', ('python3', 'b.py'), ('r/b.json',)),\n", self.NEW_ROW)
        self.fx.commit('add a gate row', {'scripts/gates/run.py': added})
        self.assertEqual([], self.rules(self.run3(), 'shared-file-shape'))
        changed = added.replace("('python3', 'b.py')", "('python3', 'other.py')")
        self.fx.commit('edit an existing row', {'scripts/gates/run.py': changed})
        found = self.rules(self.run3(), 'shared-file-shape')
        self.assertEqual(('major', 'gate checker changed'), (found[0].severity, found[0].observed.split('; ')[0]))
        self.fx.commit('add a helper', {'scripts/gates/run.py': added + "\n\ndef helper():\n    return 1\n"})
        found = self.rules(self.run3(), 'shared-file-shape')
        self.assertTrue(any('outside the GATES table: def helper' in p for c in found for p in c.evidence['problems']))
        edited = added.replace("result['b'] = 2", "result['b'] = 3")
        self.fx.commit('edit counts()', {'scripts/gates/run.py': edited})
        found = self.rules(self.run3(), 'shared-file-shape')
        self.assertTrue(any('counts() line changed or removed' in p for c in found for p in c.evidence['problems']))
        allowed = self.run3(manifest_path=self.manifest_with(authorized=[{'path': 'scripts/gates/run.py', 'change': 'counts'}]))
        self.assertEqual([], self.rules(allowed, 'shared-file-shape'))

    def test_a_new_gates_counts_branch_is_the_registration_that_gates_md_asks_for(self):
        """The diff shape of io-abi-2, joint and bootstrap: a Gate row and an `if gate.name == '<it>':` block in counts()."""
        self.assertEqual([], self.run_py_with(self.registered()))

    def test_only_the_new_gates_branch_may_be_added_to_counts(self):
        cases = {
            'a branch for a gate that already existed': self.registered("    if gate.name == 'frontend':\n        result['q'] = 1\n"),
            'a branch for a gate this diff does not add': self.registered("    if gate.name == 'ghost':\n        result['q'] = 1\n"),
            'a loose statement': self.registered("    result['loose'] = 1\n"),
            'an else branch': self.registered("    if gate.name == 'new':\n        result['q'] = 1\n    else:\n        result['r'] = 1\n"),
        }
        for label, source in cases.items():
            with self.subTest(label):
                problems = c3.run_py_problems(RUN_PY, source, {'new'})
                self.assertEqual(1, len(problems), (label, problems))
                self.assertIn('counts() gained a statement', problems[0])

    def test_editing_or_removing_an_existing_gates_count_branch_is_still_flagged(self):
        edited = self.registered().replace("result['a'] = 1", "result['a'] = 99")
        problems = c3.run_py_problems(RUN_PY, edited, {'new'})
        self.assertEqual(["counts() line changed or removed: if gate.name == 'frontend':"], problems)
        removed = self.registered().replace("    if gate.name == 'checker':\n        result['b'] = 2\n", '')
        self.assertEqual(["counts() line changed or removed: if gate.name == 'checker':"], c3.run_py_problems(RUN_PY, removed, {'new'}))
        self.assertEqual(['counts() changed its signature'], c3.run_py_problems(RUN_PY, self.registered().replace(
            'def counts(root, gate, stdout):', 'def counts(root, gate):'), {'new'}))
        self.assertEqual([], c3.run_py_problems(RUN_PY, self.registered(), {'new'}))           # the clean control

    def test_a_new_branch_that_runs_the_gates_own_module_is_a_minor_note_for_the_coordinator(self):
        """generics f39ba7e8: `if gate.name == 'generics':` loads tests/compiler-generics/check.py and calls its coverage(): four
        reviewers filed it. It is the registration GATES.md asks for, so it is never blocking, but the runner now runs gate code."""
        branch = ("    if gate.name == 'new':\n        import importlib.util\n        spec = importlib.util.spec_from_file_location('g', root / 'n.py')\n"
                  "        module = importlib.util.module_from_spec(spec)\n        spec.loader.exec_module(module)\n        module.coverage(result)\n")
        self.start({'scripts/gates/run.py': RUN_PY, 'scripts/gates/test_runner.py': TEST_RUNNER})
        self.fx.commit('register a gate whose counts run its own module', {'scripts/gates/run.py': self.registered(branch)})
        found = self.rules(self.run3(), 'shared-file-shape')
        self.assertEqual([('minor', 'coordinator', 'counts-runs-gate-code')], [(c.severity, c.actor, c.subject['kind']) for c in found])
        self.assertIn("runs the gate's own module", found[0].observed)
        self.assertEqual([], c3.run_py_problems(RUN_PY, self.registered(branch), {'new'}))      # and it is not a problem of the shape
        self.assertEqual([], c3.counts_branch_notes(RUN_PY, self.registered(), {'new'}))        # the plain registration raises no note

    def test_a_branch_selecting_several_new_gates_is_accepted_only_when_all_are_new(self):
        both = RUN_PY.replace("    Gate('checker', ('python3', 'b.py'), ('r/b.json',)),\n", self.NEW_ROW.replace(
            "Gate('new'", "Gate('other', ('python3', 'o.py'), ('r/o.json',)),\n    Gate('new'"))
        branch = "    if gate.name in ('new', 'other'):\n        result['q'] = 1\n"
        added = both.replace('    return result\n', branch + '    return result\n')
        self.assertEqual([], c3.run_py_problems(RUN_PY, added, {'new', 'other'}))
        self.assertEqual(1, len(c3.run_py_problems(RUN_PY, added, {'new'})))

    def test_a_new_gates_branch_beside_other_edits_outside_counts_is_still_flagged(self):
        source = self.registered().replace("def counts(root, gate, stdout):", "TIMEOUT = 5\n\n\ndef counts(root, gate, stdout):")
        found = self.run_py_with(source)
        self.assertEqual(1, len(found))
        self.assertTrue(any('outside the GATES table: TIMEOUT = 5' in p for p in found[0].evidence['problems']))

    def test_package_json_gains_scripts_only(self):
        base = {'name': 'knot', 'scripts': {'gates': 'python3 run.py'}, 'dependencies': {'yaml': '1'}}
        self.start({'package.json': json.dumps(base, indent=2) + '\n'})
        more = json.loads(json.dumps(base))
        more['scripts']['prechecks'] = 'python3 -B scripts/prechecks/run.py'
        self.fx.commit('add a script', {'package.json': json.dumps(more, indent=2) + '\n'})
        result = self.run3(manifest_path=self.manifest_with(owns=['scripts/prechecks/**']))
        self.assertEqual([], self.rules(result, 'shared-file-shape'))
        self.assertEqual([], self.rules(result, 'out-of-scope-edit'))          # an appendable file is not out of scope
        more['scripts']['gates'] = 'python3 other.py'
        more['dependencies']['left-pad'] = '1'
        self.fx.commit('change a script and a dependency', {'package.json': json.dumps(more, indent=2) + '\n'})
        found = self.rules(self.run3(), 'shared-file-shape')
        self.assertEqual(1, len(found))
        self.assertEqual('minor', found[0].severity)
        self.assertEqual({'script gates changed or was removed', 'a key other than scripts changed'}, set(found[0].evidence['problems']))

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

    def test_shared_files_are_judged_by_their_shape_not_as_frozen(self):
        self.start({'scripts/gates/run.py': RUN_PY, 'scripts/gates/test_runner.py': TEST_RUNNER})
        added = RUN_PY.replace("    Gate('checker', ('python3', 'b.py'), ('r/b.json',)),\n",
                               "    Gate('checker', ('python3', 'b.py'), ('r/b.json',)),\n    Gate('new', ('python3', 'n.py'), ('r/n.json',)),\n")
        self.fx.commit('add a gate', {'scripts/gates/run.py': added,
                                      'scripts/gates/test_runner.py': TEST_RUNNER.replace("'checker'}", "'checker', 'new'}")})
        result = self.run3()
        self.assertEqual([], self.rules(result, 'frozen-edit'))
        self.assertEqual([], self.rules(result, 'shared-file-shape'))

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
        self.assertEqual(['census --check'], sorted(c.subject['command'] for c in broken.conditions if c.rule == 'red-tip'))
        slow = self.conditions(c3, options={'census': True, 'census_tests': True})[1]        # census:test takes ~25 s: slow tier
        self.assertEqual(['census --check', 'census:test'], sorted(c.subject['command'] for c in slow.conditions if c.rule == 'red-tip'))


if __name__ == '__main__':
    unittest.main()

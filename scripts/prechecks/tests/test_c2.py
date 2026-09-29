import json
import unittest

from checks import c2_merge_forecast as c2
from .helpers import RepoTest

DECISIONS = '| D19 | The VM memory maximum is 65,536 pages. | why |\n'
DECISIONS_OLD = '| D19 | The VM memory maximum is 2,048 pages. | why |\n'


class C2Tests(RepoTest):
    def run2(self, **kw):
        kw.setdefault('options', {'census_after_merge': False})
        return self.conditions(c2, **kw)[1]

    def rules(self, result, rule):
        return [c for c in result.conditions if c.rule == rule]

    def manifest(self, **raw):
        path = self.fx.root.parent / 'manifest.json'
        path.write_text(json.dumps({'id': 'x', **raw}))
        return str(path)

    def diverge(self, main_files: dict, branch_files: dict, base_files=None):
        """main and the branch both start from one base commit and each add a commit."""
        self.fx.commit('base', base_files or {'src/parse.bend': 'v0\n', 'scripts/gates/run.py': 'GATES = ()\n'})
        self.fx.branch('campaign/x')
        self.fx.commit('branch work', branch_files)
        self.fx.checkout('main')
        self.fx.commit('main work', main_files)
        self.fx.checkout('campaign/x')

    # ---- clean ------------------------------------------------------------------
    def test_up_to_date_branch_is_clean(self):
        self.fx.commit('base', {'a.txt': 'a\n'})
        self.fx.branch('campaign/x')
        self.fx.commit('work', {'b.txt': 'b\n'})
        result = self.run2()
        self.assertEqual([], result.conditions)
        self.assertEqual('up-to-date', result.facts['merge_with_main'])

    def test_clean_merge_reports_only_the_behind_count(self):
        self.diverge({'docs/other.md': 'x\n'}, {'src/a.bend': 'a\n'})
        result = self.run2()
        self.assertEqual([], result.conditions)
        self.assertEqual(('clean', 1), (result.facts['merge_with_main'], result.facts['behind_main']))

    # ---- R1 ------------------------------------------------------------------------
    def test_conflict_outside_the_registry_is_major(self):
        self.diverge({'src/parse.bend': 'main\n'}, {'src/parse.bend': 'branch\n'})
        found = self.rules(self.run2(), 'conflict')
        self.assertEqual([('src/parse.bend', 'major', 'coordinator')], [(c.subject['path'], c.severity, c.actor) for c in found])

    def test_registry_conflicts_are_known_merge_conditions(self):
        base = {'src/a.bend': 'a\n', 'docs/compiler-campaign/inventory/accepted.json': '{"a": 1}\n',
                'scripts/gates/run.py': 'GATES = ()\n', 'docs/compiler-campaign/GATES.md': 'g\n'}
        self.diverge({'docs/compiler-campaign/inventory/accepted.json': '{"a": 2}\n', 'scripts/gates/run.py': 'GATES = (1,)\n',
                      'docs/compiler-campaign/GATES.md': 'g\nmain\n'},
                     {'docs/compiler-campaign/inventory/accepted.json': '{"a": 3}\n', 'scripts/gates/run.py': 'GATES = (2,)\n',
                      'docs/compiler-campaign/GATES.md': 'g\nbranch\n'}, base_files=base)
        result = self.run2()
        self.assertEqual([], self.rules(result, 'conflict'))
        self.assertEqual({'docs/compiler-campaign/inventory/accepted.json', 'scripts/gates/run.py', 'docs/compiler-campaign/GATES.md'},
                         {c.subject['path'] for c in self.rules(result, 'merge-condition')})
        self.assertEqual({'info'}, {c.severity for c in self.rules(result, 'merge-condition')})

    # ---- R2 ------------------------------------------------------------------------
    def test_sibling_conflict(self):
        self.fx.commit('base', {'src/parse.bend': 'v0\n'})
        self.fx.branch('campaign/sib')
        self.fx.commit('sibling', {'src/parse.bend': 'sib\n'})
        self.fx.checkout('main')
        self.fx.branch('campaign/x')
        self.fx.commit('mine', {'src/parse.bend': 'mine\n'})
        found = self.rules(self.run2(manifest_path=self.manifest(merge_before=['sib'])), 'sibling-conflict')
        self.assertEqual(['src/parse.bend'], [c.subject['path'] for c in found])
        self.assertEqual([], self.rules(self.run2(), 'sibling-conflict'))

    # ---- R3 ------------------------------------------------------------------------
    def test_base_fix_missing(self):
        self.diverge({'scripts/gates/run.py': 'GATES = (1,)\n', 'docs/other.md': 'x\n'}, {'src/a.bend': 'a\n'})
        found = self.rules(self.run2(), 'base-fix-missing')
        self.assertEqual(['major'], [c.severity for c in found])
        self.assertIn('scripts/gates/run.py', found[0].observed)

    def test_main_commit_on_a_path_the_branch_changed_is_minor(self):
        self.diverge({'src/shared.bend': 'main\n'}, {'src/shared.bend2': 'x\n', 'src/b.bend': 'b\n'},
                     base_files={'src/shared.bend': 'v0\n'})
        self.assertEqual([], self.rules(self.run2(), 'base-fix-missing'))
        self.fx.commit('touch shared', {'src/shared.bend': 'v0\nbranch\n'})
        found = self.rules(self.run2(), 'base-fix-missing')
        self.assertEqual(['minor'], [c.severity for c in found])

    def test_a_conflict_resolving_merge_on_main_is_listed_by_its_first_parent_diff(self):
        """`git log -- paths` lists a merge that differs from both parents there; plain diff-tree shows a merge as empty."""
        self.fx.commit('base', {'scripts/gates/run.py': 'GATES = ()\n', 'docs/a.md': 'a\n'})
        self.fx.branch('campaign/x')
        self.fx.commit('branch work', {'src/a.bend': 'a\n'})
        self.fx.checkout('main')
        self.fx.branch('side')
        self.fx.commit('side', {'docs/side.md': 's\n'})
        self.fx.checkout('main')
        self.fx.commit('main', {'docs/other.md': 'x\n'})
        self.fx.git('merge', '--no-commit', '--no-ff', 'side')
        self.fx.write('scripts/gates/run.py', 'GATES = (1,)\n')
        self.fx.git('add', '-A')
        self.fx.git('commit', '-q', '-m', 'merge side, with a gate registered')
        merge = self.fx.git('rev-parse', 'HEAD')
        self.fx.checkout('campaign/x')
        found = [c for c in self.rules(self.run2(), 'base-fix-missing') if c.subject['commit'] == merge]
        self.assertEqual(['major'], [c.severity for c in found])
        self.assertIn('scripts/gates/run.py', found[0].observed)

    def test_a_listed_commit_without_files_is_reported_and_never_crashes(self):
        from unittest import mock
        from lib.gitx import Repo
        self.diverge({'scripts/gates/run.py': 'GATES = (1,)\n'}, {'src/a.bend': 'a\n'})
        with mock.patch.object(Repo, 'commit_files', lambda self, sha: []):
            found = self.rules(self.run2(), 'base-fix-missing')
        self.assertEqual(['minor'], [c.severity for c in found])
        self.assertIn('a merged path', found[0].observed)

    # ---- R4 ------------------------------------------------------------------------
    def test_decision_drift_in_the_branch_spec(self):
        base = {'docs/COMPILER-CAMPAIGN.md': DECISIONS_OLD, 'vm/SPEC.md': '# spec\n'}
        self.diverge({'docs/COMPILER-CAMPAIGN.md': DECISIONS}, {'vm/SPEC.md': '# spec\nThe memory maximum is 2,048 pages.\n',
                                                                  'docs/notes.md': '2,048 pages\n'}, base_files=base)
        found = {c.subject['path']: c.severity for c in self.rules(self.run2(), 'decision-drift')}
        self.assertEqual({'vm/SPEC.md': 'major'}, found)          # notes.md is not a normative doc

    def test_no_decision_change_means_no_drift(self):
        base = {'docs/COMPILER-CAMPAIGN.md': DECISIONS_OLD, 'vm/SPEC.md': '# spec\n'}
        self.diverge({'docs/other.md': 'x\n'}, {'vm/SPEC.md': '# spec\n2,048 pages\n'}, base_files=base)
        self.assertEqual([], self.rules(self.run2(), 'decision-drift'))

    # ---- R5, R6 --------------------------------------------------------------------
    def upstream_fixture(self, consumer: str, **upstream_extra):
        self.fx.commit('base', {'vm/check-spec.py': 'def one_controls():\n    return []\n', 'vm/check-core.py': consumer})
        self.fx.branch('campaign/up')
        self.fx.commit('upstream adds a control set', {'vm/check-spec.py':
                       'def one_controls():\n    return []\n\ndef run_controls():\n    return []\n'})
        self.fx.checkout('main')
        self.fx.branch('campaign/x')
        self.fx.commit('downstream work', {'vm/notes.txt': 'n\n'})
        return self.manifest(upstream=[{'id': 'up', 'ref': 'campaign/up', **upstream_extra}], consumes=[
            {'file': 'vm/check-spec.py', 'pattern': r'^def (\w+_controls)\(', 'consumers': ['vm/check-core.py'],
             'not_applicable': upstream_extra.pop('not_applicable', [])}])

    def test_unconsumed_upstream_control(self):
        manifest = self.upstream_fixture('import spec\nspec.one_controls()\n')
        found = self.rules(self.run2(manifest_path=manifest), 'upstream-contract-unconsumed')
        self.assertEqual([('run_controls', 'major', 'upstream')], [(c.subject['item'], c.severity, c.actor) for c in found])

    def test_consumed_upstream_control_is_clean(self):
        manifest = self.upstream_fixture('import spec\nspec.one_controls()\nspec.run_controls()\n')
        self.assertEqual([], self.rules(self.run2(manifest_path=manifest), 'upstream-contract-unconsumed'))

    def test_merge_directed_round_makes_it_the_executors(self):
        manifest = self.upstream_fixture('import spec\n', merge=True)
        found = self.rules(self.run2(manifest_path=manifest), 'upstream-contract-unconsumed')
        self.assertEqual({'executor'}, {c.actor for c in found})

    def test_brittle_length_pin(self):
        manifest = self.upstream_fixture('import spec\n')
        self.fx.commit('pin', {'vm/check-core.py': 'import spec\nrequire(len(spec.plan_controls()) == 61, "controls")\n'})
        found = self.rules(self.run2(manifest_path=manifest), 'brittle-upstream-coupling')
        self.assertEqual(['length-pin'], [c.subject['kind'] for c in found])

    # ---- R7 ------------------------------------------------------------------------
    def test_oracle_behind(self):
        self.fx.commit('base', {'src/a.bend': 'a\n'})
        pin = self.fx.git('rev-parse', 'HEAD')
        self.fx.branch('campaign/oracle')
        self.fx.commit('oracle moves src', {'src/a.bend': 'a2\n'})
        self.fx.checkout('main')
        self.fx.branch('campaign/x')
        self.fx.commit('pins', {'vm/oracles/manifest.json': json.dumps({'pins': {'seed': {'commit': pin, 'branch': 'campaign/oracle'}}})})
        found = self.rules(self.run2(), 'oracle-behind')
        self.assertEqual(1, len(found))

    # ---- R8 ------------------------------------------------------------------------
    def test_census_after_merge(self):
        stale = "console.error('Unsupported: Stale inventory: docs/compiler-campaign/inventory/accepted.json'); process.exit(1)\n"
        self.fx.commit('base', {'tools/census/census.mjs': 'process.exit(0)\n', 'src/a.bend': 'a\n'})
        self.fx.branch('campaign/x')
        self.fx.commit('branch', {'src/a.bend': 'a2\n'})
        self.fx.checkout('main')
        self.fx.commit('main moves the census', {'tools/census/census.mjs': stale})
        self.fx.checkout('campaign/x')
        found = self.conditions(c2, options={'census_after_merge': True})[1]
        merge_conditions = [c for c in found.conditions if c.rule == 'merge-condition' and c.subject.get('path', '').endswith('inventory')]
        self.assertEqual(1, len(merge_conditions))
        self.assertEqual('coordinator', merge_conditions[0].actor)


if __name__ == '__main__':
    unittest.main()

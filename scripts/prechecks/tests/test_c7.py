import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from checks import c7_gate_adequacy as c7
from lib.model import Condition
from .helpers import RepoTest

RUN_PY = """GATES = (
    Gate('frontend', ('python3', 'tests/subsets/check_frontend.py'), ('tests/subsets/receipts/frontend.json',)),
)
"""
TEST_RUNNER = """class T:
    def test_all(self):
        self.assertLessEqual({'frontend'}, set(names))
"""


def controls(*values):
    return json.dumps({'controls': [{'name': f'c{v}', 'boundary': {'limit': 'image-words', 'value': v}} for v in values]})


class C7Tests(RepoTest):
    def start(self, files=None):
        base = {'scripts/gates/run.py': RUN_PY, 'scripts/gates/test_runner.py': TEST_RUNNER}
        base.update(files or {})
        self.fx.commit('main', base)
        self.fx.branch('campaign/x')

    def manifest(self, **raw):
        path = self.fx.root.parent / 'm.json'
        path.write_text(json.dumps({'id': 'x', **raw}))
        return str(path)

    def run7(self, **kw):
        return self.conditions(c7, **kw)[1]

    def rules(self, result, rule):
        return [c for c in result.conditions if c.rule == rule]

    def test_identity_is_clean(self):
        self.fx.commit('main', {'scripts/gates/run.py': RUN_PY})
        self.assertEqual([], self.run7().conditions)

    # ---- R1 -----------------------------------------------------------------------
    def test_limit_needs_controls_at_l_minus_one_l_and_l_plus_one(self):
        self.start({'tests/x/bounds.json': controls(99, 100, 101)})
        self.fx.commit('work', {'a.txt': 'a\n'})
        limit = {'limits': [{'name': 'image-words', 'value': 100, 'controls': ['tests/x/bounds.json']}]}
        self.assertEqual([], self.rules(self.run7(manifest_path=self.manifest(**limit)), 'limit-unwitnessed'))
        self.fx.commit('drop the boundary controls', {'tests/x/bounds.json': controls(99)})
        found = {c.subject['value']: c.severity for c in self.rules(self.run7(manifest_path=self.manifest(**limit)), 'limit-unwitnessed')}
        self.assertEqual({100: 'major', 101: 'minor'}, found)

    def test_numeric_match_without_boundary_fields_is_heuristic_and_minor(self):
        self.start({'tests/x/bounds.json': json.dumps({'rows': [99, 100]})})
        self.fx.commit('work', {'a.txt': 'a\n'})
        limit = {'limits': [{'name': 'image-words', 'value': 100, 'controls': ['tests/x/bounds.json']}]}
        found = self.rules(self.run7(manifest_path=self.manifest(**limit)), 'limit-unwitnessed')
        self.assertEqual([(101, 'minor')], [(c.subject['value'], c.severity) for c in found])
        self.assertIn('heuristic', found[0].observed)

    def test_required_value_lists(self):
        self.start({'tests/x/keys.json': controls(0, 1)})
        self.fx.commit('work', {'a.txt': 'a\n'})
        raw = {'limits': [{'name': 'image-words', 'required': [0, 1, 4294967295], 'controls': ['tests/x/keys.json']}]}
        found = self.rules(self.run7(manifest_path=self.manifest(**raw)), 'limit-unwitnessed')
        self.assertEqual([(4294967295, 'major')], [(c.subject['value'], c.severity) for c in found])

    # ---- R2 -----------------------------------------------------------------------
    def test_witness_matrix_cells(self):
        witnesses = json.dumps({'goldens': [{'cell': 'tags/Bool'}, {'cells': ['tags/Nat', 'keys/Bool']}]})
        self.start({'tests/x/goldens.json': witnesses})
        self.fx.commit('work', {'a.txt': 'a\n'})
        matrix = {'coverage': [{'name': 'case-matrix', 'axes': {'mode': ['tags', 'keys'], 'type': ['Bool', 'Nat']},
                                'witnesses': ['tests/x/goldens.json'], 'allow': [], 'must': True}]}
        found = self.rules(self.run7(manifest_path=self.manifest(**matrix)), 'witness-missing')
        self.assertEqual(['keys/Nat'], [c.subject['cell'] for c in found])
        self.assertEqual('major', found[0].severity)
        matrix['coverage'][0]['allow'] = ['keys/Nat']
        self.assertEqual([], self.rules(self.run7(manifest_path=self.manifest(**matrix)), 'witness-missing'))

    # ---- R6 -----------------------------------------------------------------------
    def test_unscaled_timeouts(self):
        self.start({'tests/y/check.py': 'x = 1\n'})
        self.fx.commit('gate', {'tests/y/check.py': "import subprocess\nTIMEOUT_SCALE = 4\n"
                                                    "subprocess.run(a, timeout=120)\n"
                                                    "subprocess.run(b, timeout=45*TIMEOUT_SCALE)\n"
                                                    "def run(argv, timeout=30):\n    pass\n"})
        found = self.rules(self.run7(), 'unscaled-timeout')
        self.assertEqual(2, len(found))
        self.assertTrue(all('SCALE' not in c.observed for c in found))

    def test_gate_headroom_uses_the_matching_gate_run(self):
        self.start({})
        self.fx.commit('work', {'b.txt': 'b\n'})
        ctx = self.fx.context()
        run_dir = self.fx.root / '.local/gates/run-1'
        run_dir.mkdir(parents=True)
        names = [n for n in ctx.head.files() if not c7.gaterun.runner_excluded(n)]
        (run_dir / 'snapshot.json').write_text(json.dumps({n: {'sha256': ctx.head.sha256(n), 'mode': 420} for n in names}))
        (run_dir / 'summary.json').write_text(json.dumps({'run': {'timeout_seconds': 900, 'gates': [
            {'name': 'fast', 'seconds': 40}, {'name': 'slow', 'seconds': 500}, {'name': 'hung', 'seconds': 800}]}}))
        found = {c.subject['gate']: (c.severity, c.actor) for c in self.rules(self.run7(), 'gate-headroom')}
        self.assertEqual({'slow': ('minor', 'coordinator'), 'hung': ('major', 'coordinator')}, found)

    # ---- R7 -----------------------------------------------------------------------
    def test_gate_wiring(self):
        self.start({})
        self.fx.commit('new gate script and row', {
            'tests/compiler-z/check.py': 'x = 1\n',
            'scripts/gates/run.py': RUN_PY.replace(')\n', "    Gate('brandnew', ('python3', 'tests/compiler-w/check.py'), ('tests/compiler-w/receipts/w.json',)),\n)\n", 1)
                                    if False else RUN_PY.rstrip(')\n') + "\n    Gate('brandnew', ('python3', 'tests/compiler-w/check.py'), ('tests/compiler-w/r.json',)),\n)\n"})
        kinds = sorted((c.subject['kind']) for c in self.rules(self.run7(), 'gate-wiring'))
        self.assertEqual(['required-name', 'unregistered-script'], kinds)

    def test_registered_gate_with_its_required_name_is_clean(self):
        self.start({})
        runner = TEST_RUNNER.replace("{'frontend'}", "{'frontend', 'brandnew'}")
        gates = RUN_PY.rstrip(')\n') + "\n    Gate('brandnew', ('python3', 'tests/compiler-w/check.py'), ('tests/compiler-w/r.json',)),\n)\n"
        self.fx.commit('gate', {'tests/compiler-w/check.py': 'x = 1\n', 'scripts/gates/run.py': gates, 'scripts/gates/test_runner.py': runner})
        self.assertEqual([], self.rules(self.run7(), 'gate-wiring'))

    # ---- R3-R5 adapters ---------------------------------------------------------------
    def test_adapters_run_only_for_a_touched_gate_and_report_failures_as_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / 'fake.py'
            good.write_text("GATE = 'fake'\nfrom lib.model import Condition\n"
                            "def touched(paths):\n    return any(p.startswith('tests/fake/') for p in paths)\n"
                            "def probe(export, ctx):\n    return [Condition('C7', 'judge-accepts-forgery', 'major', {'gate': 'fake'}, observed='survivor')]\n")
            (Path(tmp) / 'broken.py').write_text("GATE = 'broken'\ndef touched(paths):\n    return True\ndef probe(export, ctx):\n    raise ImportError('missing gate module')\n")
            self.start({})
            self.fx.commit('untouched', {'a.txt': 'a\n'})
            with mock.patch.object(c7, 'ADEQUACY_DIR', Path(tmp)):
                result = self.run7()
            self.assertEqual([], self.rules(result, 'judge-accepts-forgery'))
            self.assertIn('adequacy:broken', result.rules_unavailable)
            self.fx.commit('touch the gate', {'tests/fake/check.py': 'x = 1\n'})
            with mock.patch.object(c7, 'ADEQUACY_DIR', Path(tmp)):
                result = self.run7()
            self.assertEqual(1, len(self.rules(result, 'judge-accepts-forgery')))


if __name__ == '__main__':
    unittest.main()

import json
import os
import shutil
import unittest
from pathlib import Path

from checks import c1_probe_differential as c1
from lib import generate, oracle
from lib.lanes import Outcome, classify
from .helpers import RepoTest

REAL = Path(__file__).resolve().parents[3]
TOOLCHAIN = REAL / '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts'
HAVE_SEED = TOOLCHAIN.is_file() and shutil.which('bun') is not None


def out(kind, line='', begin=None, stdout='', code=None):
    codes = {'Checked': 0, 'Invalid': 2, 'Unsupported': 3, 'Exhausted': 4, 'HostFailure': 5, 'InternalFailure': 6}
    return Outcome(code if code is not None else codes.get(kind), kind, line, begin, stdout)


class RuleTests(unittest.TestCase):
    """The violation rules as pure functions of a seed verdict and a lane outcome: clean and broken controls."""

    def test_d4_invalid_and_its_clean_control(self):
        seed = {'parse': {'ok': True}, 'check': {'verdict': 'accept'}}
        bad = c1.violations('x', seed, {'parse': out('Invalid', 'Invalid\tparse\tx\t1:2:1:1', 1), 'check': out('Unsupported', 'Unsupported\tparse\tx\t1:2:1:1', 1)})
        self.assertEqual({('parse', 'd4-invalid')}, set(bad))
        clean = c1.violations('x', seed, {'parse': out('Checked'), 'check': out('Unsupported', 'Unsupported\tparse\tx\t1:2:1:1', 1)})
        self.assertEqual({}, clean)

    def test_unsound_accept_at_parse_check_and_eval(self):
        seed = {'parse': {'ok': False, 'beg': 4}, 'check': {'verdict': 'reject'}}
        found = c1.violations('x', seed, {'parse': out('Checked'), 'check': out('Checked'), 'eval': out('Checked', stdout='Evaluated\t0\t1\tOn{}\n')})
        self.assertEqual({('parse', 'unsound-accept'), ('check', 'unsound-accept'), ('eval', 'unsound-accept')}, set(found))
        clean = c1.violations('x', seed, {'parse': out('Invalid', 'Invalid\tparse\tx\t4:5:1:1', 4), 'check': out('Unsupported', 'Unsupported\tparse\tx\t4:5:1:1', 4)})
        self.assertEqual({}, clean)

    def test_crash_and_shape(self):
        seed = {'parse': {'ok': True}, 'check': {'verdict': 'accept'}}
        found = c1.violations('x', seed, {'parse': out('InternalFailure', 'InternalFailure\tparse\tx\t0:0:0:0'), 'check': out('crash', code=1)})
        self.assertIn(('parse', 'crash'), found)
        self.assertIn(('parse', 'diagnostic-shape'), found)            # span 0:0:0:0
        self.assertIn(('check', 'crash'), found)
        self.assertEqual({}, c1.violations('x', seed, {'parse': out('Invalid', 'Invalid\tparse\tok\t3:4:1:1', 3)} if False else {'check': out('Checked')}))
        weird = c1.violations('x', {'parse': {'ok': False, 'beg': 1}}, {'parse': out('Invalid', 'Invalid\tparse\texpected-(\t3:4:1:1', 3)})
        self.assertEqual({('parse', 'diagnostic-shape')}, set(weird))
        control = c1.violations('x', {'parse': {'ok': False, 'beg': 1}}, {'parse': out('Invalid', 'Invalid\tparse\tbad\t3:4:1:1\x07', 3)})
        self.assertIn(('parse', 'diagnostic-shape'), control)

    def test_value_disagreement_and_premature_unsupported(self):
        seed = {'check': {'verdict': 'accept'}, 'run': {'verdict': 'accept', 'stdout': 'On{}\n'}}
        bad = c1.violations('x', seed, {'eval': out('Checked', stdout='Evaluated\t0\t0\tOff{}\n')})
        self.assertEqual({('eval', 'value-disagreement')}, set(bad))
        good = c1.violations('x', seed, {'eval': out('Checked', stdout='Evaluated\t0\t1\tOn{}\n')})
        self.assertEqual({}, good)
        early = c1.violations('x', {'parse': {'ok': False, 'beg': 30}}, {'parse': out('Unsupported', 'Unsupported\tparse\tx\t10:11:1:1', 10)})
        self.assertEqual({('parse', 'premature-unsupported')}, set(early))
        late = c1.violations('x', {'parse': {'ok': False, 'beg': 30}}, {'parse': out('Unsupported', 'Unsupported\tparse\tx\t30:31:1:1', 30)})
        self.assertEqual({}, late)

    def test_inconclusive_seed_programs_are_never_flagged(self):
        self.assertEqual({}, c1.violations('x', {'parse': None, 'check': {'verdict': 'timeout'}},
                                           {'parse': out('Invalid', 'Invalid\tparse\tx\t1:2:1:1', 1), 'check': out('Invalid', 'Invalid\tparse\tx\t1:2:1:1', 1)}))

    def test_classification_of_cli_output(self):
        self.assertEqual('Invalid', classify(2, '', 'Invalid\tcheck\taffine-reuse\t3:4:1:1\n').kind)
        self.assertEqual('crash', classify(2, '', 'Unsupported\tparse\tx\t1:2:1:1\n').kind)     # class and exit disagree
        self.assertEqual('crash', classify(7, '', '').kind)
        self.assertEqual('timeout', classify(None, '', '').kind)
        self.assertEqual(('Checked', 'Evaluated\t0\t1\tOn{}\n'), (classify(0, 'Evaluated\t0\t1\tOn{}\n', '').kind, classify(0, 'Evaluated\t0\t1\tOn{}\n', '').stdout))


class GeneratorTests(unittest.TestCase):
    def test_generation_is_deterministic_and_bounded(self):
        a = generate.grid_programs(generate.quotas(120, ['src/parse.bend']), 7)
        b = generate.grid_programs(generate.quotas(120, ['src/parse.bend']), 7)
        self.assertEqual(a, b)
        self.assertLessEqual(len(a), 130)
        self.assertNotEqual(a, generate.grid_programs(generate.quotas(120, ['src/parse.bend']), 8))
        self.assertTrue({'params', 'tails', 'empty', 'let', 'binder'} <= {f for f, _k, _t in a})

    def test_operators_touch_token_boundaries(self):
        import random
        text = 'type A is Data:\n  A{x: B}\n\ndef f(x: A) -> B:\n  "s"\n'
        gaps = list(generate.gap_variants(text, 20, random.Random(1)))
        self.assertTrue(any('{' in t and t != text for _f, _k, t in gaps))
        self.assertTrue(all(t != text for _f, _k, t in gaps))
        subs = list(generate.literal_variants(text, 3, random.Random(1)))
        self.assertTrue(subs and all(t != text for _f, _k, t in subs))
        self.assertTrue(list(generate.layout_variants(text)))


@unittest.skipUnless(HAVE_SEED, 'needs the pinned seed and bun')
class EndToEndTests(RepoTest):
    """A synthetic broken head against real lanes: the classify mutant that turns Unsupported into Invalid."""

    def setUp(self):
        super().setUp()
        root = self.fx.root
        (root / '.toolchain').symlink_to(REAL / '.toolchain')
        files = {'.gitignore': '.toolchain\n'}
        for path in (REAL / 'src').glob('*.bend'):
            files[f'src/{path.name}'] = path.read_text()
        for name in ('classification-cases.json',):
            files[f'tests/subsets/{name}'] = (REAL / 'tests/subsets' / name).read_text()
        for path in (REAL / 'tests/subsets/classification').glob('*.bend'):
            files[f'tests/subsets/classification/{path.name}'] = path.read_text()
        self.fx.commit('main', files)
        self.fx.branch('campaign/x')

    def run1(self, **kw):
        kw.setdefault('options', {'c1_limit': 40, 'registry': 'none'})
        return self.conditions(c1, **kw)[1]

    def test_unchanged_sources_yield_no_new_condition(self):
        self.fx.commit('doc only', {'README.md': '# x\n'})
        result = self.run1()
        self.assertEqual('pass', result.outcome)
        self.assertEqual(0, result.facts['counts']['new'])
        self.assertGreater(result.facts['counts']['programs'], 20)

    def test_a_type_correct_mutant_that_demotes_a_seed_accepted_form_to_invalid(self):
        parse = (REAL / 'src/parse.bend').read_text()
        before, after = 'unsupported(rest,"parameter-type")', 'invalid(rest,"parameter-type")'
        self.assertEqual(1, parse.count(before))
        self.fx.commit('demote application parameters', {'src/parse.bend': parse.replace(before, after)})
        result = self.run1()
        found = [c for c in result.conditions if c.rule == 'd4-invalid' and c.subject['lane'] == 'parse']
        self.assertTrue(found, [c.line() for c in result.conditions][:5])
        fixture = [c for c in found if c.value['family'] == 'fixture']     # the tracked classification fixture is among them
        self.assertTrue(fixture, [c.value for c in found])
        self.assertEqual({'blocking'}, {c.severity for c in found})       # major, raised one step: a regression
        self.assertTrue(any('parameter-type' in c.evidence['knot'] for c in fixture))
        again = self.run1(base=self.fx.git('rev-parse', 'HEAD'))           # against itself: the same violation is known, not new
        self.assertEqual([], [c for c in again.conditions if c.rule == 'd4-invalid'])

    def test_incomplete_repair_needs_the_declared_target_family(self):
        gap = 'type Flag is Data:\n  Off{}\n  On{}\n\ndef f?(x: Flag) -> Flag:\n  x\n\ndef main() -> Flag:\n  f(On{})\n'
        row = {'kind': 'lang', 'family': 'test-gap', 'text': gap, 'sha256': c1.sha(gap), 'source': {'cited': 'def-marker'},
               'seed': {'parse': 'ok', 'check': 'accept', 'run': 'accept', 'stdout': 'On{}\n'}}
        self.fx.commit('a registry row that is a known D4 gap at the base', {'tests/prechecks/registry/lang.jsonl': json.dumps(row) + '\n'})
        manifest = self.fx.root.parent / 'm.json'
        manifest.write_text(json.dumps({'id': 'x', 'd4_targets': ['test-gap']}))
        result = self.run1(manifest_path=str(manifest))
        repair = [c for c in result.conditions if c.rule == 'incomplete-repair']
        self.assertTrue(repair)
        self.assertEqual('major', repair[0].severity)
        self.assertGreaterEqual(result.facts['d4_gap_count'], 1)                 # the gap is a known fact either way
        plain = self.run1()
        self.assertEqual([], [c for c in plain.conditions if c.rule == 'incomplete-repair'])
        self.assertEqual(0, plain.facts['counts']['new'])


if __name__ == '__main__':
    unittest.main()

import json
import os
import shutil
import unittest
from pathlib import Path
from unittest import mock

import freeze
from checks import c1_probe_differential as c1
from lib import generate, oracle
from lib.lanes import Outcome, classify
from lib.seed import Seed
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

    def test_value_disagreement(self):
        seed = {'check': {'verdict': 'accept'}, 'run': {'verdict': 'accept', 'stdout': 'On{}\n'}}
        bad = c1.violations('x', seed, {'eval': out('Checked', stdout='Evaluated\t0\t0\tOff{}\n')})
        self.assertEqual({('eval', 'value-disagreement')}, set(bad))
        good = c1.violations('x', seed, {'eval': out('Checked', stdout='Evaluated\t0\t1\tOn{}\n')})
        self.assertEqual({}, good)

    def test_premature_unsupported_is_the_recognized_token_being_the_rejected_token(self):
        seed = {'parse': {'ok': False, 'beg': 30}}
        at = c1.violations('x', seed, {'parse': out('Unsupported', 'Unsupported\tparse\ttemplate-binder\t30:31:1:1', 30)})
        self.assertEqual({('parse', 'premature-unsupported')}, set(at))
        self.assertNotIn('raise', at[('parse', 'premature-unsupported')])           # a regression: the ratchet raises it
        # The clean controls: the same program reported Invalid, or Unsupported at a valid prefix that the SPEC lists.
        self.assertEqual({}, c1.violations('x', seed, {'parse': out('Invalid', 'Invalid\tparse\tparameter\t30:31:1:1', 30)}))
        prefix = out('Unsupported', 'Unsupported\tparse\ttype-application\t10:11:1:1', 10)
        self.assertEqual({}, c1.violations('x', seed, {'parse': prefix}, frozenset({'type-application'})))

    def test_a_valid_prefix_is_documented_policy_only_when_the_spec_lists_its_code(self):
        seed = {'parse': {'ok': False, 'beg': 30}}
        prefix = out('Unsupported', 'Unsupported\tparse\ttype-application\t10:11:1:1', 10)
        found = c1.violations('x', seed, {'parse': prefix})                              # no SPEC table at all
        self.assertEqual({('parse', 'premature-unsupported')}, set(found))
        self.assertEqual(False, found[('parse', 'premature-unsupported')]['raise'])     # a documentation gap: minor, never raised
        self.assertEqual({}, c1.violations('x', seed, {'parse': prefix}, frozenset({'type-application', 'import'})))
        other = c1.violations('x', seed, {'parse': prefix}, frozenset({'import'}))         # the SPEC lists other codes only
        self.assertEqual({('parse', 'premature-unsupported')}, set(other))

    def test_a_span_after_the_seed_error_and_non_ascii_text_are_not_judged_by_offsets(self):
        seed = {'parse': {'ok': False, 'beg': 30}}
        after = out('Unsupported', 'Unsupported\tparse\ttype-application\t44:45:1:1', 44)   # the seed backtracked to 30
        self.assertEqual({}, c1.violations('x', seed, {'parse': after}))
        at = out('Unsupported', 'Unsupported\tparse\ttemplate-binder\t30:31:1:1', 30)
        self.assertEqual({}, c1.violations('caf\u00e9', seed, {'parse': at}))
        self.assertEqual({}, c1.violations('x', {'parse': {'ok': False, 'beg': None}}, {'parse': at}))

    def test_a_probe_frozen_as_malformed_must_stay_invalid_whatever_the_offsets_say(self):
        seed = {'parse': {'ok': False, 'beg': 118}, 'expect': {'parse': 'Invalid'}}
        early = out('Unsupported', 'Unsupported\tparse\tdestructuring-binding\t116:117:9:14', 116)   # the `=>` after a constructor
        found = c1.violations('x', seed, {'parse': early}, frozenset({'destructuring-binding'}))
        self.assertEqual({('parse', 'premature-unsupported')}, set(found))
        self.assertEqual({}, c1.violations('x', seed, {'parse': out('Invalid', 'Invalid\tparse\tend-of-body\t116:117:9:14', 116)}))
        self.assertEqual({('parse', 'unsound-accept')}, set(c1.violations('x', seed, {'parse': out('Checked')})))

    def test_the_confirmed_programs_are_flagged_by_the_seed_error_offset_alone(self):
        """A non-leading `~x`, `Name<` read as less-than in a return type and in an annotation: the seed's error is at the
        recognized token, so the offsets alone (no `expect`) flag the tip's Unsupported and not the base's Invalid."""
        rows = {row['source']['cited']: row for row in c1.tool_rows()}
        for cited, code in (('.local/probes/template-second.bend', 'template-binder'), ('r1-return-lt.bend', 'type-application'),
                            ('r2b-annot-spaced-lt.bend', 'type-application')):
            with self.subTest(program=cited):
                row = rows[cited]
                offset = row['seed']['offset']
                verdicts = {'parse': {'ok': False, 'beg': offset}}
                tip = out('Unsupported', f'Unsupported\tparse\t{code}\t{offset}:{offset + 1}:1:1', offset)
                base = out('Invalid', f'Invalid\tparse\tparameter\t{offset}:{offset + 1}:1:1', offset)
                self.assertEqual({('parse', 'premature-unsupported')},
                                 set(c1.violations(row['text'], verdicts, {'parse': tip}, frozenset({code}))))
                self.assertNotIn('raise', c1.violations(row['text'], verdicts, {'parse': tip}, frozenset({code}))[('parse', 'premature-unsupported')])
                self.assertEqual({}, c1.violations(row['text'], verdicts, {'parse': base}, frozenset({code})))

    def test_the_confirmed_classify_regressions_are_flagged_from_the_registry(self):
        """The reviewers' confirmed at-prefix programs, frozen in the registry: the tip's Unsupported must be flagged and
        the base's Invalid must not (the tips' spans are the ones the reviewers recorded)."""
        rows = {row['source']['cited']: row for row in c1.tool_rows()}
        cases = {'.local/probes/template-second.bend': ('template-binder', 57), 'r1-return-lt.bend': ('type-application', 53),
                 'r2b-annot-spaced-lt.bend': ('type-application', 65), 'd3_eqeq.bend': ('destructuring-binding', 66),
                 'd11_ctor_lambda.bend': ('destructuring-binding', 116)}
        for cited, (code, begin) in cases.items():
            with self.subTest(program=cited):
                row = rows[cited]
                verdicts = {'parse': {'ok': False, 'beg': row['seed']['offset']}, 'expect': row['expect']}
                tip = out('Unsupported', f'Unsupported\tparse\t{code}\t{begin}:{begin + 1}:1:1', begin)
                base = out('Invalid', f'Invalid\tparse\tend-of-body\t{begin}:{begin + 1}:1:1', begin)
                self.assertEqual({('parse', 'premature-unsupported')}, set(c1.violations(row['text'], verdicts, {'parse': tip}, frozenset({code}))))
                self.assertEqual({}, c1.violations(row['text'], verdicts, {'parse': base}))

    def test_the_spec_prefix_table_is_read_from_the_tree(self):
        class Tree:
            def __init__(self, text):
                self.body = text

            def text(self, path):
                return self.body if path == 'src/SPEC.md' else None
        table = ('The parser recognizes these prefixes.\n\n| Recognized form | Phase | Code |\n| --- | --- | --- |\n'
                 '| Leading `~name:` in a parameter list | `parse` | `template-binder` |\n'
                 '| `import ./...` or `import 0x.../...` | `parse` | `import` |\n\n')
        self.assertEqual(frozenset({'template-binder', 'import'}), c1.prefix_codes(Tree(table + 'Recognition stops at that prefix.\n')))
        self.assertEqual(frozenset(), c1.prefix_codes(Tree(table)))                     # not a prefix-only table
        self.assertEqual(frozenset(), c1.prefix_codes(Tree('')))

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


class FrozenCorpusTests(unittest.TestCase):
    """The fast tier judges the same programs, with the same frozen seed verdicts, on every head, base and host."""

    def test_the_frozen_verdicts_cover_exactly_the_generated_programs(self):
        # No seed runs here: the sha256 of every generated program is looked up in tests/prechecks/registry/seed-verdicts.jsonl.
        self.assertEqual([], freeze.verify())

    def test_the_fast_corpus_is_a_function_of_the_registry_and_constants_only(self):
        rows = c1.tool_rows()
        plain = c1.build_corpus(rows, rows, [])
        focused = c1.build_corpus(rows, rows, [], changed_sources=['src/parse.bend', 'src/check.bend'])
        self.assertEqual(list(plain), list(focused))                       # the changed sources do not steer the fast sample
        self.assertEqual(list(plain), list(c1.build_corpus(rows, rows, [])))
        fixture = {'family': 'fixture', 'text': 'def only_here() -> U32:\n  1\n', 'seed': {'check': 'accept'}, 'source': 'tests/x.bend'}
        with_fixture = c1.build_corpus(rows, rows, [fixture])
        self.assertEqual(set(plain) | {c1.sha(fixture['text'])}, set(with_fixture))   # a tree's fixtures add themselves, nothing else
        self.assertLessEqual(len(plain), len(rows) + generate.GRID_TOTAL + generate.OPERATOR_TOTAL)

    def test_the_slow_corpus_is_larger_and_follows_the_changed_sources(self):
        rows = c1.tool_rows()
        slow = c1.build_corpus(rows, rows, [], slow=True, changed_sources=['src/parse.bend'])
        self.assertGreater(len(slow), len(c1.build_corpus(rows, rows, [])))

    def test_frozen_rows_name_the_pinned_seed_and_carry_a_verdict_for_every_parsed_program(self):
        frozen = c1.load_frozen()
        self.assertGreater(len(frozen), 500)
        for digest, seed in frozen.items():
            self.assertIn(seed['parse'], ('ok', 'reject', 'skipped'), digest)
            if seed['parse'] == 'ok':
                self.assertIn(seed['check'], ('accept', 'reject', 'crash', 'timeout'), digest)

    def test_a_seed_revision_that_is_not_the_pinned_one_is_ignored(self):
        import tempfile
        rows = [{'sha256': 'a' * 64, 'seed_revision': 'not-the-pin', 'seed': {'parse': 'ok', 'check': 'accept'}},
                {'sha256': 'b' * 64, 'seed_revision': c1.SEED_REVISION, 'seed': {'parse': 'ok', 'check': 'accept'}}]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'v.jsonl'
            path.write_text(''.join(json.dumps(r) + '\n' for r in rows))
            with mock.patch.object(c1, 'TOOL_VERDICTS', path):
                self.assertEqual({'b' * 64}, set(c1.load_frozen()))


class LaneAvailabilityTests(RepoTest):
    """A check that cannot look never reports a pass: an unavailable family L is a named gap, not `not-applicable`."""

    def start(self):
        self.fx.commit('main', {'src/parse-cli.bend': 'def main() -> U32:\n  0\n', 'src/check-cli.bend': 'def main() -> U32:\n  0\n'})
        self.fx.branch('campaign/x')
        self.fx.commit('work', {'README.md': '# x\n'})

    def test_a_missing_seed_or_bun_is_unavailable_never_not_applicable(self):
        self.start()
        with mock.patch.object(Seed, 'available', return_value=False):
            result = self.conditions(c1, options={'registry': 'none'})[1]
        self.assertEqual('unavailable', result.outcome)
        self.assertIn('seed', result.reason)
        with mock.patch.object(Seed, 'available', return_value=True), mock.patch.object(c1.shutil, 'which', return_value=None):
            result = self.conditions(c1, options={'registry': 'none'})[1]
        self.assertEqual(('unavailable', True), (result.outcome, 'bun' in result.reason))

    def test_an_unavailable_family_l_stays_a_named_gap_beside_family_v(self):
        files = {'src/parse-cli.bend': 'def main() -> U32:\n  0\n', 'src/check-cli.bend': 'def main() -> U32:\n  0\n',
                 'vm/serializer.py': FAKE_CODEC, 'vm/registry.json': '{}\n', 'vm/golden/a.plan.json': plan()}
        self.fx.commit('main', files)
        self.fx.branch('campaign/x')
        self.fx.commit('work', {'README.md': '# x\n'})
        with mock.patch.object(Seed, 'available', return_value=False):
            result = self.conditions(c1, options={'registry': 'none'})[1]
        self.assertEqual('partial', result.outcome)                                  # family V ran and found nothing: not a pass
        self.assertIn('family-l', result.rules_unavailable)
        self.assertIn('reference-crash', result.rules_run)


FAKE_CODEC = """import json

class Malformed(Exception):
    pass

class Exhausted(Exception):
    pass

def registry(path=None):
    return {'registry': 1}

def base_digest(reg):
    return b'digest'

def encode(plan, digest):
    if plan.get('mode') == 'crash':
        return None.to_bytes(1, 'little')          # the d2fe0f20 failure: an AttributeError on a none-typed node
    if plan.get('mode') == 'malformed':
        raise Malformed('bad image')
    if plan.get('mode') == 'refused':
        raise ValueError('not a plan')
    return json.dumps(plan).encode()

def decode(data, digest):
    plan = json.loads(data)
    if plan.get('mode') == 'lossy':
        plan.pop('extra', None)
    return plan

def validate(plan, registry):
    return []
"""


def plan(**fields):
    return json.dumps({'entry': 'book', **fields})


class FamilyVTests(RepoTest):
    """R11 and R12 over the reference codec of the tree, with a fake codec so that every outcome is deliberate."""

    def start(self, goldens: dict, codec=FAKE_CODEC):
        files = {'vm/serializer.py': codec, 'vm/registry.json': '{}\n'}
        files.update({f'vm/golden/{name}.plan.json': text for name, text in goldens.items()})
        self.fx.commit('main', files)
        self.fx.branch('campaign/x')

    def run5(self):
        return self.conditions(c1, options={'registry': 'none'})[1]

    def test_clean_goldens_and_declared_refusals_raise_nothing(self):
        self.start({'a': plan(), 'b': plan(mode='malformed'), 'c': plan(mode='refused')})
        self.fx.commit('work', {'README.md': '# x\n'})
        result = self.run5()
        self.assertEqual([], result.conditions)
        self.assertEqual(3, result.facts['family_v']['plans'])
        self.assertIn('family L', ' '.join(result.notes))

    def test_a_new_crash_of_the_reference_is_major_and_an_old_one_is_known(self):
        self.start({'a': plan()})
        self.fx.commit('a golden that crashes the encoder', {'vm/golden/crash.plan.json': plan(mode='crash')})
        found = [c for c in self.run5().conditions if c.rule == 'reference-crash']
        self.assertEqual(1, len(found))
        self.assertEqual(('major', 'executor'), (found[0].severity, found[0].actor))
        self.assertIn('AttributeError', found[0].observed)
        self.fx.commit('unrelated', {'README.md': '# x\n'})
        again = self.conditions(c1, options={'registry': 'none'}, base=self.fx.git('rev-parse', 'HEAD'))[1]
        self.assertEqual([], again.conditions)                                # the same crash at base is known
        self.assertEqual(1, again.facts['family_v']['known'])

    def test_roundtrip_is_judged_on_goldens_only(self):
        self.start({'a': plan()})
        self.fx.commit('lossy golden', {'vm/golden/lossy.plan.json': plan(mode='lossy', extra=1)})
        found = [c for c in self.run5().conditions if c.rule == 'roundtrip']
        self.assertEqual(['vm/golden/lossy.plan.json'], [c.evidence['plan'] for c in found])

    def test_a_tree_without_a_codec_is_not_applicable(self):
        self.fx.commit('main', {'a.txt': 'a\n'})
        self.fx.branch('campaign/x')
        self.fx.commit('work', {'b.txt': 'b\n'})
        self.assertEqual('not-applicable', self.run5().outcome)


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
        files['src/SPEC.md'] = (REAL / 'src/SPEC.md').read_text()          # its prefix-only table names the documented recognizers
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
        self.assertEqual('partial', result.outcome)                       # nothing found, but two rules could not run: never `pass`
        self.assertEqual({'helper-divergence', 'incomplete-repair'}, set(result.rules_unavailable))
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

    def test_a_mutant_that_reports_the_seeds_error_token_as_unsupported_is_a_regression(self):
        """The classify regression: a non-leading `~x` (the seed's error is at the `~`) moves from Invalid to Unsupported."""
        parse = (REAL / 'src/parse.bend').read_text()
        before = 'Bool.and(parameters,starts(t,"~")),u =>\n              invalid(t,"parameter"),u =>'
        after = 'Bool.and(parameters,starts(t,"~")),u =>\n              unsupported(t,"template-binder"),u =>'
        self.assertEqual(1, parse.count(before))
        row = next(r for r in c1.tool_rows() if r['source']['cited'] == '.local/probes/template-second.bend')     # the reviewer's program
        self.fx.commit('report a tilde after an ordinary binder as a template binder',
                       {'src/parse.bend': parse.replace(before, after), 'tests/prechecks/registry/lang.jsonl': json.dumps(row) + '\n'})
        result = self.run1(options={'c1_limit': 70, 'registry': 'none'})
        found = [c for c in result.conditions if c.rule == 'premature-unsupported']
        self.assertTrue(found, [c.line() for c in result.conditions][:5])
        self.assertEqual({'major'}, {c.severity for c in found})           # minor, raised one step: base said Invalid
        self.assertEqual({'executor'}, {c.actor for c in found})
        frozen = [c for c in found if 'template-second.bend' in c.observed]
        self.assertEqual(1, len(frozen), [c.line() for c in found])       # the reviewer's confirmed program, from the registry
        self.assertIn("the seed's error token", ' '.join(c.observed for c in found if c not in frozen))     # and the grid programs
        self.assertEqual({'d4-invalid', 'unsound-accept'} & {c.rule for c in result.conditions}, set())
        again = self.run1(options={'c1_limit': 70, 'registry': 'none'}, base=self.fx.git('rev-parse', 'HEAD'))
        self.assertEqual([], [c for c in again.conditions if c.rule == 'premature-unsupported'])

    def test_a_recognized_prefix_that_the_spec_lists_is_policy_not_a_condition(self):
        """Before classify, a leading `~name:` was Invalid; after it, Unsupported at the prefix while the seed rejects the
        program later (`~a: Flag, ~b: List<Flag>`). The SPEC table lists the code, so that is D4's documented policy."""
        parse = (REAL / 'src/parse.bend').read_text()
        recognizer = 'unsupported(ts,"template-binder"),u => invalid(ts,"parameter"))'
        self.assertEqual(1, parse.count(recognizer))
        self.fx.checkout('main')
        self.fx.commit('before classify: no recognizer', {'src/parse.bend': parse.replace(recognizer, 'invalid(ts,"parameter"),u => invalid(ts,"parameter"))')})
        self.fx.branch('campaign/z')
        self.fx.commit('add the recognizer', {'src/parse.bend': parse})
        result = self.run1(options={'c1_limit': 70, 'registry': 'none'})
        self.assertEqual([], [c.line() for c in result.conditions if c.rule == 'premature-unsupported'])
        self.assertGreater(result.facts['prefix_policy'].get('template-binder', 0), 0)      # counted as a fact, never as a condition
        self.assertIn('template-binder', result.facts['spec_prefix_codes'])

    def test_the_conditions_do_not_depend_on_the_commit_the_cache_or_a_documentation_only_change(self):
        parse = (REAL / 'src/parse.bend').read_text()
        before = 'unsupported(rest,"parameter-type")'
        self.fx.commit('demote', {'src/parse.bend': parse.replace(before, 'invalid(rest,"parameter-type")')})

        def fingerprints(result):
            return sorted((c.fingerprint, c.severity) for c in result.conditions), result.facts['counts']['programs']

        cold = fingerprints(self.run1())
        warm = fingerprints(self.run1())                                   # same commit, warm caches
        self.fx.commit('a different commit with the same sources', {'docs/note.md': 'changed\n'})
        docs_only = fingerprints(self.run1())                              # another commit id, another whole tree, the same src
        import shutil as _shutil
        _shutil.rmtree(self.fx.scratch)                                      # a cold cache again
        cold_again = fingerprints(self.run1())
        self.assertTrue(cold[0])
        self.assertEqual(cold, warm)
        self.assertEqual(cold, docs_only)
        self.assertEqual(cold, cold_again)

    def test_a_head_whose_lane_does_not_build_is_a_condition_never_a_pass(self):
        cli = (REAL / 'src/parse-cli.bend').read_text()
        self.fx.commit('break the parse lane', {'src/parse-cli.bend': cli + '\ndef broken( -> :\n'})
        result = self.run1()
        self.assertEqual('conditions', result.outcome)
        found = [c for c in result.conditions if c.rule == 'lane-build']
        self.assertEqual(1, len(found))
        self.assertEqual(('major', 'executor', {'lane': 'parse'}), (found[0].severity, found[0].actor, found[0].subject))
        self.assertIn('family-l', result.rules_unavailable)
        broken_base = self.fx.git('rev-parse', 'HEAD')
        self.fx.commit('work on the broken lane', {'README.md': '# y\n'})
        against_broken = self.run1(base=broken_base)                       # the base does not build either: nothing to blame
        self.assertEqual([], [c for c in against_broken.conditions if c.rule == 'lane-build'])
        self.assertEqual('unavailable', against_broken.outcome)

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

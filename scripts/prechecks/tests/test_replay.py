import contextlib
import io
import json
import re
import unittest
from pathlib import Path

import replay
from lib import ledger as ledger_mod
from lib.model import Condition
from .helpers import RepoTest

TABLE = json.loads(replay.DEFAULT_TABLE.read_text(encoding='utf-8'))
LEDGER = json.loads((replay.DEFAULT_TABLE.parent / TABLE['ledger']).read_text(encoding='utf-8'))


def report(*rows):
    """A report with one check whose conditions are (check, rule, severity, actor, status) rows."""
    return {'checks': [{'conditions': [{'check': c, 'rule': r, 'severity': s, 'actor': a, 'ledger': {'status': st}}
                                       for c, r, s, a, st in rows]}]}


class ReplayLogicTests(unittest.TestCase):
    def test_residual_counts_only_unacknowledged_executor_majors(self):
        rows = [('C1', 'premature-unsupported', 'major', 'executor', 'new'), ('C1', 'premature-unsupported', 'major', 'executor', 'new'),
                ('C3', 'frozen-edit', 'blocking', 'executor', 'changed'), ('C4', 'host-path', 'major', 'executor', 'known'),
                ('C4', 'host-path', 'major', 'coordinator', 'new'), ('C5', 'composition-budget', 'minor', 'executor', 'new')]
        self.assertEqual({'C1.premature-unsupported': 2, 'C3.frozen-edit': 1}, replay.residual(report(*rows)))
        self.assertEqual({}, replay.residual(report()))

    def test_compare_names_every_difference(self):
        context = {'default': {'exit': 3, 'executor_major': {'C4.host-path': 1}}, 'with_ledger': {'exit': 0, 'executor_major': {}}}
        self.assertEqual([], replay.compare(context, {'exit': 3, 'executor_major': {'C4.host-path': 1}}, {'exit': 0, 'executor_major': {}}))
        problems = replay.compare(context, {'exit': 0, 'executor_major': {}}, {'exit': 3, 'executor_major': {'C4.host-path': 1}})
        self.assertEqual(4, len(problems))
        self.assertIn('default: exit 0, expected 3', problems)


class ControlTableTests(unittest.TestCase):
    def test_every_context_names_full_commits_and_both_expectations(self):
        names = [c['name'] for c in TABLE['contexts']]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual({'classify', 'classify-2', 'joint', 'bootstrap', 'census-2', 'recursion', 'poly', 'sugar', 'io-abi-2'},
                         set(names) - {'main-25b3a5b6'})
        for context in TABLE['contexts']:
            with self.subTest(context['name']):
                for key in ('head', 'main_ref') + (('base',) if context.get('base') else ()):
                    self.assertRegex(context[key], r'^[0-9a-f]{40}$')
                self.assertIn(context['kind'], ('clean', 'broken'))
                for policy in ('default', 'with_ledger'):
                    self.assertIn(context[policy]['exit'], (0, 3))
                    self.assertEqual(context[policy]['exit'] == 3, bool(context[policy]['executor_major']))

    def test_clean_controls_end_clean_with_the_ledger_and_broken_controls_never_do(self):
        for context in TABLE['contexts']:
            with self.subTest(context['name']):
                ended_clean = context['with_ledger']['exit'] == 0
                self.assertEqual(context['kind'] == 'clean', ended_clean)

    def test_the_confirmed_defects_are_never_ledgered(self):
        for context in TABLE['contexts']:
            if context['kind'] == 'broken':
                self.assertTrue(context['with_ledger']['executor_major'], context['name'])
        rules = {(e['check'], e['rule']) for e in LEDGER['entries']}
        self.assertFalse({r for r in rules if r[0] == 'C1'}, 'a regression that the reviewers confirmed must not be acknowledged')

    def test_the_proposed_ledger_is_well_formed_and_pinned_to_measured_values(self):
        self.assertIn('never read by the suite', LEDGER['note'])
        seen = set()
        for entry in LEDGER['entries']:
            with self.subTest(entry['subject']):
                condition = Condition(entry['check'], entry['rule'], 'major', entry['subject'])
                self.assertEqual(condition.fingerprint, entry['fingerprint'])          # the fingerprint is recomputable from the subject
                self.assertEqual('coordinator', entry['owner'])
                self.assertTrue(entry['reason'] and entry['value'] is not None)
                self.assertNotIn(entry['fingerprint'], seen)
                seen.add(entry['fingerprint'])
                self.assertIn(entry['increment'], {c['name'] for c in TABLE['contexts']})

    def test_the_suite_never_reads_the_proposed_ledger_by_itself(self):
        self.assertNotIn('proposed', ledger_mod.LEDGER_PATH)
        self.assertEqual('docs/compiler-campaign/known-conditions.json', ledger_mod.LEDGER_PATH)


class ReplayCliTests(RepoTest):
    def test_a_context_whose_commits_are_absent_is_skipped_and_reported(self):
        self.fx.commit('main', {'a.txt': 'a\n'})
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = replay.main(['--repo', str(self.fx.root), '--only', 'classify,poly'])
        self.assertEqual(0, code)
        lines = out.getvalue().strip().splitlines()
        self.assertEqual(['classify', 'poly'], [line.split()[0] for line in lines])
        self.assertTrue(all('skipped: the campaign history is not in this repository' in line for line in lines))


if __name__ == '__main__':
    unittest.main()

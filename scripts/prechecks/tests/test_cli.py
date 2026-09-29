import contextlib
import io
import json
import unittest
from unittest import mock

import checks as checks_mod
import run as run_mod
from lib.model import CheckResult, Condition
from lib.runner import Check
from .helpers import RepoTest


def cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = run_mod.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class CliTests(RepoTest):
    def branch_with_host_path(self):
        self.fx.commit('main', {'a.txt': 'a\n'})
        self.fx.branch('campaign/x')
        self.fx.commit('receipt', {'tests/compiler-x/receipts/x.json': json.dumps({'status': 'passed', 'out': '/private/tmp/x/build'})})

    def base_args(self):
        return ['--repo', str(self.fx.root), '--out', str(self.fx.scratch / 'out'), '--only', 'C4', '--json']

    def test_exit_3_on_a_new_executor_condition_and_json_is_the_only_stdout(self):
        self.branch_with_host_path()
        code, out, err = cli(*self.base_args())
        self.assertEqual(3, code)
        report = json.loads(out)                           # nothing but the report on stdout
        self.assertEqual(3, report['exit'])
        self.assertEqual('conditions', report['checks'][0]['outcome'])
        self.assertIn('C4 receipt-integrity', err)         # progress goes to stderr
        for name in ('report.json', 'report.md', 'facts.json', 'known.txt'):
            self.assertTrue((self.fx.scratch / 'out' / name).is_file(), name)

    def test_fail_on_and_the_actor_decide_the_exit_code(self):
        self.branch_with_host_path()
        self.assertEqual(0, cli(*self.base_args(), '--fail-on', 'blocking')[0])
        self.assertEqual(0, cli(*self.base_args(), '--fail-on', 'none')[0])
        self.assertEqual(3, cli(*self.base_args(), '--fail-on', 'minor')[0])

    def test_known_conditions_are_subtracted_by_the_ledger_from_main(self):
        self.branch_with_host_path()
        code, out, _ = cli(*self.base_args())
        entries = json.loads(cli(*self.base_args(), '--emit-ledger')[1])
        self.assertTrue(entries and all(e['fingerprint'] and e['owner'] == 'coordinator' for e in entries))
        ledger = self.fx.root.parent / 'ledger.json'
        ledger.write_text(json.dumps({'entries': entries}))
        code, out, _ = cli(*self.base_args(), '--ledger', str(ledger))
        self.assertEqual(0, code)
        self.assertEqual({'known'}, {c['ledger']['status'] for c in json.loads(out)['checks'][0]['conditions']})

    def test_coordinator_conditions_never_fail_the_run(self):
        self.fx.commit('base', {'src/parse.bend': 'v0\n'})
        self.fx.branch('campaign/x')
        self.fx.commit('mine', {'src/parse.bend': 'mine\n'})
        self.fx.checkout('main')
        self.fx.commit('theirs', {'src/parse.bend': 'theirs\n'})
        self.fx.checkout('campaign/x')
        code, out, _ = cli('--repo', str(self.fx.root), '--only', 'C2', '--json', '--no-write')
        report = json.loads(out)
        conflicts = [c for c in report['checks'][0]['conditions'] if c['rule'] == 'conflict']
        self.assertEqual(('major', 'coordinator'), (conflicts[0]['severity'], conflicts[0]['actor']))
        self.assertEqual(0, code)

    def test_a_crashing_check_is_exit_1_never_a_silent_pass(self):
        self.fx.commit('main', {'a.txt': 'a\n'})
        self.fx.branch('campaign/x')
        self.fx.commit('work', {'b.txt': 'b\n'})

        def boom(ctx):
            raise RuntimeError('boom')
        broken = Check('C4', 'receipt-integrity', 'x', boom)
        with mock.patch.object(checks_mod, 'load', lambda only=None, skip=None: [broken]):
            code, out, _ = cli('--repo', str(self.fx.root), '--json', '--no-write')
        self.assertEqual(1, code)
        self.assertEqual('error', json.loads(out)['checks'][0]['outcome'])

    def test_usage_errors_and_listing(self):
        self.assertEqual(2, cli('--repo', str(self.fx.root.parent), '--json')[0])       # not a repository
        self.fx.commit('main', {'a.txt': 'a\n'})
        self.assertEqual(2, cli('--repo', str(self.fx.root), '--head', 'no-such-rev', '--json')[0])
        code, out, _ = cli('--list')
        self.assertEqual(0, code)
        self.assertEqual(['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8'], [line.split()[0] for line in out.strip().splitlines()])

    def test_uncommitted_and_untracked_files_are_judged(self):
        self.fx.commit('main', {'a.txt': 'a\n'})
        self.fx.branch('campaign/x')
        self.fx.write('tests/compiler-x/receipts/x.json', json.dumps({'status': 'passed', 'out': '/private/tmp/x'}))   # never committed
        code, out, _ = cli(*self.base_args())
        self.assertEqual(3, code)
        self.assertTrue(json.loads(out)['head']['worktree'])


if __name__ == '__main__':
    unittest.main()

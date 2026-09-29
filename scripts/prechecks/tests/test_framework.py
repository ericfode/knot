import json
import os
import threading
import time
import unittest
from unittest import mock

from lib import globs
from lib import report as report_mod
from lib import runner as runner_mod
from lib.effbase import compute
from lib.model import CheckResult, Condition, fingerprint, raised
from lib import ledger as ledger_mod
from lib.runner import Check
from .helpers import RepoTest


class GlobTests(unittest.TestCase):
    def test_globs(self):
        cases = [('tests/**/expectations*.json', 'tests/a/b/expectations.json', True),
                 ('tests/**/expectations*.json', 'tests/expectations-2.json', True),
                 ('tests/**/expectations*.json', 'src/expectations.json', False),
                 ('**/receipts/*.json', 'tests/x/receipts/a.json', True),
                 ('**/receipts/*.json', 'receipts/a.json', True),
                 ('a/*/c', 'a/b/x/c', False),
                 ('{src,tests}/**', 'tests/x/y', True),
                 ('scripts/gates/**', 'scripts/gates/run.py', True),
                 ('*.md', 'docs/x.md', False)]
        for pattern, path, expected in cases:
            with self.subTest(pattern=pattern, path=path):
                self.assertEqual(expected, globs.match(pattern, path))


class ModelTests(unittest.TestCase):
    def test_fingerprint_ignores_value_and_line_numbers(self):
        a = Condition('C4', 'host-path', 'major', {'path': 'a.json', 'pointer': '/x'}, value={'hits': 1})
        b = Condition('C4', 'host-path', 'major', {'path': 'a.json', 'pointer': '/x'}, value={'hits': 9})
        self.assertEqual(a.fingerprint, b.fingerprint)
        self.assertNotEqual(a.fingerprint, fingerprint('C4', 'host-path', {'path': 'b.json', 'pointer': '/x'}))
        self.assertEqual('blocking', raised('major'))
        self.assertEqual('blocking', raised('blocking'))

    def test_ledger_status_known_changed_new(self):
        c = Condition('C5', 'preflight-new-blocker', 'minor', {'target': 'x::Digest'}, value=3)
        ledger = ledger_mod.Ledger([{'fingerprint': c.fingerprint, 'owner': 'coordinator', 'reason': 'pinned'}])
        ledger.annotate([c])
        self.assertEqual('known', c.status)          # no value key: any value is acknowledged
        ledger = ledger_mod.Ledger([{'fingerprint': c.fingerprint, 'value': 3, 'reason': 'r'}])
        ledger.annotate([c])
        self.assertEqual('known', c.status)
        c.value = 4
        ledger.annotate([c])
        self.assertEqual('changed', c.status)
        ledger = ledger_mod.Ledger([{'fingerprint': c.fingerprint, 'until': '2000-01-01'}])
        ledger.annotate([c])
        self.assertEqual('new', c.status)


class ContextTests(RepoTest):
    def test_identity_on_main(self):
        self.fx.commit('one', {'a.txt': 'a\n'})
        ctx = self.fx.context()
        self.assertTrue(ctx.identity)
        self.assertEqual(ctx.base_commit, ctx.head_commit)
        self.assertEqual([], ctx.changes())
        self.assertEqual([], ctx.commits())

    def test_branch_base_is_merge_base_and_worktree_is_snapshotted(self):
        self.fx.commit('one', {'a.txt': 'a\n', 'gone.txt': 'x\n'})
        base = self.fx.git('rev-parse', 'HEAD')
        self.fx.branch('campaign/demo')
        self.fx.commit('two', {'b.txt': 'b\n'})
        self.fx.write('a.txt', 'a edited\n')            # uncommitted edit
        self.fx.write('new.txt', 'untracked\n')          # untracked, not ignored
        self.fx.write('.env', 'SYNTHETIC=1\n')           # never staged, even without .gitignore
        self.fx.remove('gone.txt')
        ctx = self.fx.context()
        self.assertEqual('demo', ctx.inc)
        self.assertEqual(base, ctx.base_commit)
        self.assertTrue(ctx.worktree and ctx.dirty)
        self.assertEqual(['a.txt', 'b.txt', 'new.txt'], ctx.changed_paths())
        self.assertEqual(['gone.txt'], ctx.deleted_paths())
        self.assertNotIn('.env', ctx.head.files())
        self.assertEqual('a edited\n', ctx.head.text('a.txt'))
        self.assertEqual(['two'], [c.subject for c in ctx.commits()])

    def test_head_option_uses_a_committed_revision(self):
        self.fx.commit('one', {'a.txt': 'a\n'})
        self.fx.branch('campaign/x')
        first = self.fx.commit('two', {'a.txt': 'two\n'})
        self.fx.commit('three', {'a.txt': 'three\n'})
        ctx = self.fx.context(head=first)
        self.assertEqual('two\n', ctx.head.text('a.txt'))
        self.assertFalse(ctx.worktree)

    def test_effective_base_of_a_stacked_increment(self):
        self.fx.commit('main', {'m.txt': 'm\n'})
        self.fx.branch('campaign/up')
        self.fx.commit('up work', {'up.txt': 'u\n'})
        self.fx.branch('campaign/down')
        self.fx.commit('down work', {'down.txt': 'd\n'})
        repo = self.fx.repo()
        up_tip = repo.rev_parse('campaign/up')
        plain = compute(repo, repo.rev_parse('HEAD'), 'main', [])
        stacked = compute(repo, repo.rev_parse('HEAD'), 'main', [{'id': 'up', 'ref': 'campaign/up'}])
        self.assertEqual(repo.rev_parse('main'), plain.commit)
        self.assertEqual(up_tip, stacked.commit)
        self.assertEqual('stacked', stacked.kind)
        ctx = self.fx.context(upstream=['up'])
        self.assertEqual(['down.txt'], ctx.changed_paths())


class OutcomeTests(RepoTest):
    """`pass` means every rule ran and found nothing; a gap is never reported as a pass."""

    def test_finish_distinguishes_pass_partial_and_conditions(self):
        self.assertEqual('pass', CheckResult().finish().outcome)
        partial = CheckResult(rules_unavailable={'gate-run': 'no summary'}).finish()
        self.assertEqual(('partial', True), (partial.outcome, partial.incomplete))
        found = CheckResult(conditions=[Condition('C4', 'host-path', 'major', {'path': 'a'})], rules_unavailable={'x': 'y'}).finish()
        self.assertEqual(('conditions', True), (found.outcome, found.incomplete))
        for outcome in ('unavailable', 'not-applicable', 'error'):
            self.assertEqual(outcome, CheckResult(outcome=outcome, rules_unavailable={'x': 'y'}).finish().outcome)
        self.assertTrue(CheckResult(outcome='unavailable').incomplete)
        self.assertFalse(CheckResult(outcome='not-applicable').incomplete)

    def outcomes(self, *results):
        return [runner_mod.Outcome(Check(f'C{i}', f'check{i}', 't', None), r.finish(), 0.1) for i, r in enumerate(results, 1)]

    def test_exit_policy_only_strict_turns_a_gap_into_exit_4(self):
        gap = CheckResult(rules_unavailable={'gate-run': 'no summary'})
        clean = CheckResult()
        failing = CheckResult(conditions=[Condition('C4', 'host-path', 'major', {'path': 'a'})])
        broken = CheckResult(outcome='error', reason='boom')
        codes = lambda *r, strict=False: runner_mod.summarize(self.outcomes(*r), 'major', strict)['exit']
        self.assertEqual(0, codes(clean, gap))                      # the default lets the implementer proceed, and says so
        self.assertEqual(4, codes(clean, gap, strict=True))
        self.assertEqual(0, codes(clean, strict=True))
        self.assertEqual(3, codes(gap, failing, strict=True))       # a failing condition outranks a gap
        self.assertEqual(1, codes(failing, broken, gap, strict=True))
        self.assertEqual(4, codes(CheckResult(outcome='unavailable', reason='no bun'), strict=True))

    def test_reports_name_every_rule_that_did_not_run(self):
        self.fx.commit('main', {'a.txt': 'a\n'})
        fx = self.fx.context()
        results = [CheckResult(rules_run=['a'], rules_unavailable={'gate-run': 'no summary | with a pipe'}),
                   CheckResult(outcome='unavailable', reason='timeout after 9s'), CheckResult(rules_run=['b'])]
        outcomes = self.outcomes(*results)
        text = report_mod.text(fx, outcomes)
        self.assertIn('partial', text)
        self.assertIn('not run  gate-run: no summary | with a pipe', text)
        self.assertIn('2 check(s) with a rule or check that did not run', text)
        markdown = report_mod.markdown(fx, outcomes)
        self.assertIn('## Checks and rules that did not run (never a pass)', markdown)
        self.assertIn('C1 `gate-run`: no summary | with a pipe', markdown)
        self.assertIn('C2 check2: unavailable: timeout after 9s', markdown)
        rows = [line for line in markdown.splitlines() if line.startswith('| C')]
        self.assertTrue(all(line.replace('\\|', '').count('|') == 7 for line in rows), rows)      # every table row keeps its cells
        facts = report_mod.facts_json(fx, outcomes)
        self.assertEqual({'gate-run': 'no summary | with a pipe'}, facts['coverage']['C1']['rules_unavailable'])
        self.assertEqual('unavailable', facts['coverage']['C2']['outcome'])
        self.assertEqual('pass', facts['coverage']['C3']['outcome'])
        self.assertEqual(2, report_mod.to_json(fx, outcomes)['summary']['incomplete'])

    def test_a_reason_with_a_pipe_or_a_line_break_cannot_split_a_table_row(self):
        self.assertEqual('parse: 60 \\| ok', report_mod.cell('parse: 60 |\n  ok'))


class HangGuardTests(RepoTest):
    def test_an_overrunning_check_is_unavailable_and_actually_stops(self):
        """The guard cancels the check: tools die with their process group and queued tool runs are never started."""
        from concurrent.futures import ThreadPoolExecutor
        self.fx.commit('main', {'a.txt': 'a\n'})
        started, finished = [], threading.Event()

        def slow(ctx):
            def one(i):
                started.append(i)
                return ctx.run(['sleep', '30'], timeout=120)[0]
            try:
                with ThreadPoolExecutor(max_workers=2) as pool:
                    list(pool.map(one, range(12)))
            finally:
                finished.set()
            return CheckResult(rules_run=['slow'])

        check = Check('CX', 'slow', 'a check that overruns', slow, budget=4)
        began = time.monotonic()
        with mock.patch.dict(os.environ, {'KNOT_GATE_TIMEOUT_SCALE': '0.05'}):        # a 0.2 s budget
            outcomes = runner_mod.execute([check], self.fx.context())
        reported = time.monotonic() - began
        self.assertEqual('unavailable', outcomes[0].result.outcome)
        self.assertIn('timeout after', outcomes[0].result.reason)
        self.assertLess(reported, 3)
        self.assertTrue(finished.wait(5), 'the queued tool runs kept the check alive after the guard gave up')
        self.assertLess(time.monotonic() - began, 6)                 # not 12 sleeps of 30 s on two workers

    def test_a_tool_that_outlives_its_timeout_is_killed_with_its_children(self):
        from lib import proc
        code, out, err = proc.run(['sh', '-c', 'sleep 30 & sleep 30; wait'], timeout=0.3)
        self.assertEqual((None, b'timeout'), (code, err))
        self.assertEqual((None, b'cancelled'), proc.run(['sleep', '1'], cancel=self._raised())[::2])
        code, out, err = proc.run(['sh', '-c', 'cat; echo done'], input=b'hello\n', timeout=5)
        self.assertEqual((0, b'hello\ndone\n'), (code, out))

    @staticmethod
    def _raised():
        event = threading.Event()
        event.set()
        return event


class IncrementIdTests(RepoTest):
    def test_the_same_commit_gets_the_same_increment_from_every_checkout(self):
        self.fx.commit('main', {'a.txt': 'a\n'})
        self.fx.branch('campaign/y')
        tip = self.fx.commit('y work', {'y.txt': 'y\n'})
        self.fx.checkout('main')
        self.fx.branch('campaign/x')                       # the invoking checkout sits on another campaign branch
        self.fx.commit('x work', {'x.txt': 'x\n'})
        self.assertEqual('y', self.fx.context(head=tip).inc)             # named by the one campaign ref whose tip it is
        self.assertEqual('x', self.fx.context().inc)                     # the working copy is judged as the checkout's branch
        self.assertEqual('y', self.fx.context(head='campaign/y').inc)
        self.fx.checkout('main')
        self.assertEqual('y', self.fx.context(head=tip).inc)

    def test_a_commit_no_campaign_ref_names_has_no_increment_and_none_is_explicit(self):
        first = self.fx.commit('main', {'a.txt': 'a\n'})
        self.fx.branch('campaign/x')
        self.fx.commit('x work', {'x.txt': 'x\n'})
        self.assertIsNone(self.fx.context(head=first).inc)               # never the invoking branch's id
        self.assertEqual('x', self.fx.context(head=first, inc='x').inc)
        self.assertIsNone(self.fx.context(head=first, inc='none').inc)
        self.assertIsNone(self.fx.context(inc='none').inc)


class SnapshotTests(RepoTest):
    def shared(self):
        (self.fx.root.parent / 'shared').mkdir(exist_ok=True)
        for name in ('.toolchain', 'node_modules'):
            (self.fx.root / name).symlink_to(self.fx.root.parent / 'shared')          # GATES.md: worktrees share these as links
        self.fx.write('.local/x/y.txt', 'scratch\n')
        self.fx.write('build/out.txt', 'generated\n')
        self.fx.write('.env', 'SYNTHETIC_ONLY=1\n')
        self.fx.write('.env.local', 'SYNTHETIC_ONLY=2\n')

    def test_shared_symlinks_and_generated_directories_do_not_make_a_worktree_dirty(self):
        self.fx.commit('main', {'a.txt': 'a\n'})
        head_tree = self.fx.git('rev-parse', 'HEAD^{tree}')
        self.shared()
        repo = self.fx.repo()
        self.assertFalse(repo.worktree_dirty())
        self.assertEqual(head_tree, repo.snapshot_worktree())
        self.assertFalse(self.fx.context().dirty)
        self.fx.write('b.txt', 'new\n')                                             # a real change still counts
        self.assertTrue(repo.worktree_dirty())
        self.assertNotEqual(head_tree, repo.snapshot_worktree())

    def test_the_snapshot_works_when_the_excluded_names_are_ignored_and_exist(self):
        """`git add -A -- . ':(exclude).env'` fails when `.env` exists and is ignored (a main checkout; `.local` in every
        worktree): the exclusions are wildcard globs, never named paths, and nothing excluded is staged or read."""
        self.fx.commit('main', {'a.txt': 'a\n', '.gitignore': '.env\n.env.*\n.toolchain/\nnode_modules/\n.local/\nbuild/\n'})
        head_tree = self.fx.git('rev-parse', 'HEAD^{tree}')
        self.shared()
        self.fx.write('sub/.env', 'SYNTHETIC_ONLY=3\n')
        repo = self.fx.repo()
        self.assertEqual(head_tree, repo.snapshot_worktree())
        self.assertFalse(repo.worktree_dirty())
        self.fx.write('b.txt', 'new\n')
        tree = repo.snapshot_worktree()
        self.assertEqual(['a.txt', 'b.txt'], sorted(p for p in repo.ls_tree(tree) if not p.startswith('.gitignore')))
        self.assertNotIn('.env', repo.ls_tree(tree))

    def test_a_nested_directory_named_build_is_not_excluded(self):
        self.fx.commit('main', {'tests/x/build/keep.txt': 'v1\n'})
        self.fx.write('tests/x/build/keep.txt', 'v2\n')
        self.assertTrue(self.fx.repo().worktree_dirty())
        self.assertNotEqual(self.fx.git('rev-parse', 'HEAD^{tree}'), self.fx.repo().snapshot_worktree())


if __name__ == '__main__':
    unittest.main()

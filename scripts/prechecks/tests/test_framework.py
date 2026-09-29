import json
import os
import unittest

from lib import globs
from lib.effbase import compute
from lib.model import Condition, fingerprint, raised
from lib import ledger as ledger_mod
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


if __name__ == '__main__':
    unittest.main()

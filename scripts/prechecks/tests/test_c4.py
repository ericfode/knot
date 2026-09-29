import hashlib
import json
import shutil
import unittest
from pathlib import Path
from unittest import mock

from checks import c4_receipt_integrity as c4
from .helpers import RepoTest


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def receipt(**fields) -> str:
    return json.dumps({'status': 'passed', **fields}, indent=2) + '\n'


class C4Tests(RepoTest):
    def branch_from(self, files: dict):
        self.fx.commit('main', files)
        self.fx.branch('campaign/x')

    def rules(self, result, rule):
        return [c for c in result.conditions if c.rule == rule]

    # ---- clean controls -------------------------------------------------
    def test_identity_is_clean(self):
        self.fx.commit('main', {'tests/compiler-x/receipts/x.json': receipt(path='/Users/eric/x')})
        _, result = self.conditions(c4)
        self.assertEqual([], result.conditions)          # pre-existing host paths on main never fire

    def test_untouched_legacy_host_paths_do_not_fire(self):
        self.branch_from({'packages/p/receipts/old.json': receipt(path='/Users/eric/x'), 'a.txt': 'a\n'})
        self.fx.commit('unrelated', {'a.txt': 'b\n'})
        _, result = self.conditions(c4)
        self.assertEqual([], result.conditions)

    def test_the_rules_that_read_changed_receipts_have_nothing_to_check_when_none_changed(self):
        self.branch_from({'packages/p/receipts/old.json': receipt(path='/Users/eric/x'), 'a.txt': 'a\n'})
        self.fx.commit('unrelated', {'a.txt': 'b\n'})
        _, result = self.conditions(c4)
        for rule in c4.CHANGED_RULES:
            self.assertIn('no receipt was added or changed', result.rules_na[rule])
        self.assertTrue({'unowned-receipt-drift-predicted', 'corpus-glob-coupling'} <= set(result.rules_run))
        self.fx.commit('a receipt', {'tests/compiler-x/receipts/x.json': receipt()})
        _, changed = self.conditions(c4)
        self.assertEqual({}, changed.rules_na)                     # once a receipt changes, all four rules run
        self.assertTrue(set(c4.CHANGED_RULES) <= set(changed.rules_run))

    # ---- R1 host-path -----------------------------------------------------
    def test_host_path_in_new_receipt(self):
        self.branch_from({'a.txt': 'a\n'})
        self.fx.commit('receipt', {'tests/compiler-x/receipts/x.json':
                                   receipt(build={'out': '/private/tmp/claude-501/x/build.js'}, ok='$ROOT/src/a.bend')})
        _, result = self.conditions(c4)
        found = self.rules(result, 'host-path')
        self.assertEqual(1, len(found))
        self.assertEqual(('major', 'executor', 1), (found[0].severity, found[0].actor, found[0].value['hits']))

    def test_host_path_tokenized_receipt_is_clean(self):
        self.branch_from({'a.txt': 'a\n'})
        self.fx.commit('receipt', {'tests/compiler-x/receipts/x.json':
                                   receipt(build='$ROOT/.local/x', seed='.toolchain/bend/main.ts', lib='$BEND_LIB/0xabc')})
        _, result = self.conditions(c4)
        self.assertEqual([], self.rules(result, 'host-path'))

    def test_worktree_and_toolchain_symlink_paths(self):
        self.branch_from({'a.txt': 'a\n'})
        self.fx.commit('receipt', {'research/y/receipts/gate.json':
                                   receipt(a='/x/.claude/worktrees/campaign-y/src', b='../../.toolchain/seed/base.bend')})
        _, result = self.conditions(c4)
        self.assertEqual(1, len(self.rules(result, 'host-path')))
        self.assertEqual(2, self.rules(result, 'host-path')[0].value['hits'])

    def test_host_path_added_to_a_legacy_receipt_fires_as_coordinator_condition(self):
        self.branch_from({'packages/p/receipts/old.json': receipt(path='/Users/eric/a')})
        self.fx.commit('edit', {'packages/p/receipts/old.json': receipt(path='/Users/eric/a', more='/Users/eric/b')})
        _, result = self.conditions(c4)
        found = self.rules(result, 'host-path')
        self.assertEqual(1, len(found))
        self.assertEqual('coordinator', found[0].actor)      # unowned receipt: not the executor's to fix

    # ---- R2 stale hashes --------------------------------------------------
    def test_stale_hash_fires_and_fresh_hash_is_clean(self):
        src = 'def f():\n  1\n'
        self.branch_from({'src/a.bend': src, 'tests/compiler-x/receipts/x.json':
                          receipt(inputs={'src/a.bend': sha(src)})})
        new = 'def f():\n  2\n'
        self.fx.commit('edit source only', {'src/a.bend': new, 'tests/compiler-x/receipts/x.json':
                                            receipt(inputs={'src/a.bend': sha(src)}, note='touched')})
        _, result = self.conditions(c4)
        found = self.rules(result, 'stale-receipt-hash')
        self.assertEqual(1, len(found))
        self.assertEqual(['src/a.bend'], found[0].evidence['inputs'])
        self.fx.commit('refresh', {'tests/compiler-x/receipts/x.json': receipt(inputs={'src/a.bend': sha(new)}, note='touched')})
        _, result = self.conditions(c4)
        self.assertEqual([], self.rules(result, 'stale-receipt-hash'))

    RUN_PY = "GATES = (\n    Gate('x', ('python3', 'tests/compiler-x/check.py'), ('tests/compiler-x/receipts/x.json',)),\n)\n"

    def stale_receipt(self, receipt_text, extra=None):
        src = 'def f():\n  1\n'
        self.branch_from({'src/a.bend': src, 'src/b.bend': 'def g():\n  1\n', **(extra or {})})
        self.fx.commit('edit both sources and add the receipt', {'src/a.bend': 'def f():\n  2\n', 'src/b.bend': 'def g():\n  2\n',
                                                                 'tests/compiler-x/receipts/x.json': receipt_text})
        return self.conditions(c4)[1]

    def test_a_pre_implementation_freeze_section_is_history_not_staleness(self):
        """recursion's reference.json: `baseline_implementation` is written once, before the implementation, under
        `require(not receipt.exists(), 'the freeze is immutable')`; regenerating it would break the freeze."""
        old = {'src/a.bend': sha('def f():\n  1\n'), 'src/b.bend': sha('def g():\n  1\n')}
        now = {'src/a.bend': sha('def f():\n  2\n'), 'src/b.bend': sha('def g():\n  2\n')}
        result = self.stale_receipt(receipt(baseline_implementation=old, frozen_inputs=now, inputs=now), {'scripts/gates/run.py': self.RUN_PY})
        self.assertEqual([], self.rules(result, 'stale-receipt-hash'))
        self.assertEqual(2, result.facts['historical_hash_claims'])

    def test_a_stale_current_input_section_of_a_registered_output_is_major(self):
        registered = self.stale_receipt(receipt(inputs={'src/a.bend': sha('def f():\n  1\n')}), {'scripts/gates/run.py': self.RUN_PY})
        found = self.rules(registered, 'stale-receipt-hash')
        self.assertEqual(('major', 'executor'), (found[0].severity, found[0].actor))
        self.assertNotIn('no gate regenerates', found[0].observed)
        self.assertIn('never a baseline or freeze section', found[0].fix_hint)

    def test_a_stale_current_input_section_of_a_receipt_no_gate_regenerates_is_minor(self):
        unregistered = self.stale_receipt(receipt(inputs={'src/a.bend': sha('def f():\n  1\n')}))
        found = self.rules(unregistered, 'stale-receipt-hash')
        self.assertEqual(('minor', 'executor'), (found[0].severity, found[0].actor))
        self.assertIn('no gate regenerates this receipt', found[0].observed)

    def test_a_freeze_beside_a_stale_current_section_reports_only_the_current_one(self):
        old = {'src/a.bend': sha('def f():\n  1\n'), 'src/b.bend': sha('def g():\n  1\n')}
        result = self.stale_receipt(receipt(baseline_implementation=old, inputs={'src/a.bend': sha('def f():\n  1\n')}),
                                    {'scripts/gates/run.py': self.RUN_PY})
        found = self.rules(result, 'stale-receipt-hash')
        self.assertEqual(['src/a.bend'], found[0].evidence['inputs'])
        self.assertEqual(2, result.facts['historical_hash_claims'])

    def test_provenance_sections_are_recognized_by_name(self):
        for pointer, expected in (('/baseline_implementation/src~1a.bend', True), ('/x_at_freeze/p', True), ('/audit/inputs/p', True),
                                  ('/candidate-wasm/p', True), ('/latest_target_hashes/p', True), ('/prior_project_baseline/p', True),
                                  ('/inputs/src~1a.bend', False), ('/frozen_inputs/p', False), ('/files/0/sha256', False),
                                  ('/source_hashes/p', False), ('/checked_inputs_sha256/p', False)):
            with self.subTest(pointer=pointer):
                self.assertEqual(expected, c4.is_provenance(pointer))

    def test_hash_already_stale_at_base_is_not_re_reported(self):
        self.branch_from({'src/a.bend': 'v2\n', 'tests/compiler-x/receipts/x.json': receipt(inputs={'src/a.bend': sha('v1\n')})})
        self.fx.commit('unrelated edit', {'tests/compiler-x/receipts/x.json':
                                          receipt(inputs={'src/a.bend': sha('v1\n')}, note='n')})
        _, result = self.conditions(c4)
        self.assertEqual([], self.rules(result, 'stale-receipt-hash'))

    def test_record_shape_with_path_and_sha256(self):
        self.branch_from({'src/a.bend': 'x\n'})
        self.fx.commit('r', {'tests/compiler-x/receipts/x.json': receipt(files=[{'path': 'src/a.bend', 'sha256': sha('other')}])})
        _, result = self.conditions(c4)
        self.assertEqual(1, len(self.rules(result, 'stale-receipt-hash')))

    def test_decorative_hash(self):
        self.branch_from({'tests/compiler-x/check.py': "record = {}\nrecord['unread_sha256'] = digest(x)\n"})
        self.fx.commit('r', {'tests/compiler-x/receipts/x.json': receipt(unread_sha256=sha('a'))})
        _, result = self.conditions(c4)
        self.assertEqual(1, len(self.rules(result, 'decorative-hash')))
        self.fx.commit('reads it', {'tests/compiler-x/check.py':
                                    "record['unread_sha256'] = digest(x)\nrequire(record['unread_sha256'] == digest(y))\n"})
        _, result = self.conditions(c4)
        self.assertEqual([], self.rules(result, 'decorative-hash'))

    # ---- R3 predicted drift and corpus coupling ------------------------------
    def test_predicted_drift_names_unowned_receipts(self):
        src = 'v1\n'
        self.branch_from({'src/a.bend': src, 'tests/compiler-checker/receipts/checker.json': receipt(inputs={'src/a.bend': sha(src)})})
        self.fx.commit('edit', {'src/a.bend': 'v2\n'})
        _, result = self.conditions(c4)
        found = self.rules(result, 'unowned-receipt-drift-predicted')
        self.assertEqual(1, len(found))
        self.assertEqual(('info', 'coordinator'), (found[0].severity, found[0].actor))

    def test_added_bend_enters_bootstrap_corpus(self):
        self.branch_from({'tests/compiler-bootstrap/check.py': '# gate\n'})
        self.fx.commit('add', {'tests/compiler-x/f.bend': 'def main(): 1\n'})
        _, result = self.conditions(c4)
        self.assertEqual(1, len(self.rules(result, 'corpus-glob-coupling')))

    # ---- R5 volatility ------------------------------------------------------
    def test_measurements_docs_duplicates_and_orphans(self):
        self.branch_from({'a.txt': 'a\n', 'README.md': '# x\n'})
        blob = receipt(peak_rss_bytes=123, inputs={'README.md': sha('# x\n')})
        self.fx.commit('receipts', {'tests/compiler-x/receipts/a.json': blob, 'tests/compiler-x/receipts/b.json': blob})
        _, result = self.conditions(c4)
        kinds = sorted(c.subject.get('kind') for c in self.rules(result, 'receipt-volatility'))
        self.assertEqual(['doc-input', 'doc-input', 'measurement', 'measurement'], kinds)
        self.assertEqual(1, len(self.rules(result, 'receipt-duplicate')))
        self.assertEqual(2, len(self.rules(result, 'receipt-orphan')))

    def test_orphan_is_cleared_by_registration(self):
        run_py = ("from dataclasses import dataclass\nGATES = (\n    Gate('x', ('python3', 'tests/compiler-x/check.py'),\n"
                  "         ('tests/compiler-x/receipts/*.json',)),\n)\n")
        self.branch_from({'scripts/gates/run.py': run_py})
        self.fx.commit('receipt', {'tests/compiler-x/receipts/a.json': receipt(ok=True)})
        _, result = self.conditions(c4)
        self.assertEqual([], self.rules(result, 'receipt-orphan'))

    def test_preflight_flood(self):
        self.branch_from({'a.txt': 'a\n'})
        self.fx.commit('many', {f'tests/compiler-x/receipts/preflight-{i}.json': receipt(n=i) for i in range(5)})
        _, result = self.conditions(c4)
        self.assertEqual(1, len(self.rules(result, 'receipt-flood')))

    # ---- R6 date-only receipt commits -----------------------------------------
    def test_date_only_receipt_commit(self):
        self.branch_from({'a.txt': 'a\n', 'tests/compiler-x/receipts/x.json': receipt(date='2026-09-28T01:00:00+00:00', n=1)})
        self.fx.commit('date only', {'tests/compiler-x/receipts/x.json': receipt(date='2026-09-28T02:00:00+00:00', n=1)})
        self.fx.commit('real change', {'tests/compiler-x/receipts/x.json': receipt(date='2026-09-28T03:00:00+00:00', n=2)})
        _, result = self.conditions(c4)
        found = self.rules(result, 'receipt-date-only')
        self.assertEqual(1, len(found))
        self.assertEqual('coordinator', found[0].actor)

    def test_the_fast_normalizer_answers_exactly_as_the_gates_normalizer(self):
        from lib import gates as gates_lib
        normalize = gates_lib.load_module('normalize')
        base = normalize.Normalizer(Path('/nonexistent-prechecks-root'))
        fast = c4.fast_normalizer(normalize)
        strings = ['', 'plain', 'a/b/c', '/nonexistent-prechecks-root/src/a.bend', 'x /nonexistent-prechecks-root/y z',
                   '../../.toolchain/bend/main.ts', '/Users/me/checkout/.toolchain/bend-2.0.29/x', '$ROOT/.toolchain/./y',
                   '.bend/lib/Base', '/home/u/.bend/lib/Base/List', '$BEND_LIB/./a', '$ROOT', 'sha256:abc', '2026-09-28T01:00:00Z',
                   '/other/checkout/scripts/x.py', 'toolchain', '.toolchain', '$BEND']
        for aliases in ({str(base.root): '$ROOT'}, {str(base.root): '$ROOT', '/other/checkout': '$ROOT'}, {'': '$ROOT'}):
            for text in strings:
                self.assertEqual(base.text(text, aliases), fast.text(text, aliases), (text, aliases))
        value = {'date': '2026-09-28T01:00:00+00:00', 'argv': ['/x/scripts/bend-reference', '/x/src/a.bend'], 'elapsed_seconds': 3.5,
                 'p': '/x/.toolchain/a', '/x/key': ['plain', '/x/.bend/lib/Base']}
        data = json.dumps(value).encode()
        self.assertEqual(base.receipt('r.json', data, {}), fast.receipt('r.json', data, {}))

    # ---- R4 the implementer's own gate run -----------------------------------------
    def write_run(self, ctx, receipts, gates):
        head = ctx.head
        names = [n for n in head.files() if not c4.runner_excluded(n)]
        run_dir = self.fx.root / '.local/gates/run-abc'
        run_dir.mkdir(parents=True)
        (run_dir / 'snapshot.json').write_text(json.dumps({n: {'sha256': head.sha256(n), 'mode': 420} for n in names}))
        (run_dir / 'summary.json').write_text(json.dumps({'normalized': {'gates': gates, 'receipts': receipts}}))

    def test_gate_run_drift_and_red_gate(self):
        self.branch_from({'a.txt': 'a\n'})
        self.fx.commit('work', {'b.txt': 'b\n'})
        ctx = self.fx.context()
        self.write_run(ctx, [{'path': 'tests/compiler-checker/receipts/checker.json', 'classification': 'semantic',
                              'changed_fields': ['/inputs/src~1a.bend']},
                             {'path': 'tests/compiler-x/receipts/x.json', 'classification': 'semantic'},
                             {'path': 'tests/other/receipts/y.json', 'classification': 'volatile-only'}],
                       [{'name': 'checker', 'status': 'passed'}, {'name': 'wasm', 'status': 'failed'}])
        ctx = self.fx.context(options={'use_gate_run': True})
        result = c4.CHECK.run(ctx).finish()
        self.assertEqual(['gate-red', 'own-receipt-stale', 'unowned-receipt-drift'],
                         sorted(c.rule for c in result.conditions if c.rule in ('gate-red', 'own-receipt-stale', 'unowned-receipt-drift')))
        drift = [c for c in result.conditions if c.rule == 'unowned-receipt-drift'][0]
        self.assertEqual(('major', 'coordinator'), (drift.severity, drift.actor))

    def test_the_slow_tier_runs_the_gates_itself_but_the_fast_tier_never_does(self):
        self.branch_from({'scripts/gates/run.py': 'GATES = ()\n', 'a.txt': 'a\n'})
        self.fx.commit('work', {'b.txt': 'b\n'})
        for tier, expected in (('fast', 0), ('slow', 1)):
            ctx = self.fx.context(tier=tier)
            calls = []

            def fake_run(argv, **kwargs):
                calls.append([str(a) for a in argv])
                self.write_run(ctx, [{'path': 'tests/compiler-checker/receipts/checker.json', 'classification': 'semantic'}],
                               [{'name': 'checker', 'status': 'passed'}])
                return 0, b'', b''

            with mock.patch.object(ctx, 'run', fake_run):
                result = c4.CHECK.run(ctx).finish()
            self.assertEqual(expected, len(calls), tier)
            if expected:
                self.assertIn('scripts/gates/run.py', calls[0][-1])
                self.assertTrue([c for c in result.conditions if c.rule == 'unowned-receipt-drift'])
            else:
                self.assertIn('gate-run', result.rules_unavailable)
            shutil.rmtree(self.fx.root / '.local', ignore_errors=True)

    def test_gate_run_of_a_different_snapshot_is_unavailable_not_a_pass(self):
        self.branch_from({'a.txt': 'a\n'})
        self.fx.commit('work', {'b.txt': 'b\n'})
        ctx = self.fx.context()
        self.write_run(ctx, [], [])
        self.fx.commit('later edit', {'c.txt': 'c\n'})
        _, result = self.conditions(c4)
        self.assertIn('gate-run', result.rules_unavailable)
        self.assertIn('predates', result.rules_unavailable['gate-run'])


if __name__ == '__main__':
    unittest.main()

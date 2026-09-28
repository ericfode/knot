"""Independent literal controls and executable semantic mutants for the wrapper."""
import gzip
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import threading
import types
import unittest
from unittest.mock import patch

import normalize
import run


HERE = Path(__file__).resolve().parent
EXPECT = json.loads((HERE / 'fixtures/expectations.json').read_bytes())


def encoded(value):
    return json.dumps(value).encode()


class ReceiptTests(unittest.TestCase):
    def test_literal_classifications(self):
        normalizer = normalize.Normalizer(Path('/new/checkout'))
        for case in EXPECT['receipt_cases']:
            with self.subTest(case=case['name']):
                before, after = encoded(case['before']), encoded(case['after'])
                self.assertEqual(case['expected'], normalize.classify(before, after,
                    normalizer.receipt('gate.json', before, {}), normalizer.receipt('gate.json', after, {})))

    def test_gzip_headers_and_payload(self):
        normalizer = normalize.Normalizer(Path('/new/checkout'))
        original = io.BytesIO()
        with gzip.GzipFile(fileobj=original, filename='old.txt', mode='wb', mtime=12345) as stream:
            stream.write(b'Off{}\n')
        a, b = original.getvalue(), normalize.pack(b'Off{}\n')
        normalized = lambda data: normalizer.receipt('observations.txt.gz', data, {})
        self.assertEqual(EXPECT['gzip']['headers_only'], normalize.classify(a, b, normalized(a), normalized(b)))
        c = normalize.pack(b'On{}\n')
        self.assertEqual(EXPECT['gzip']['payload_change'], normalize.classify(b, c, normalized(b), normalized(c)))
        self.assertEqual(b, normalized(normalized(a)))
        self.assertEqual(0, int.from_bytes(b[4:8], 'little'))
        self.assertEqual(255, b[9])

    def test_gzip_digest_edge_requires_matching_bytes(self):
        path = 'research/flat-store/receipts/gate.json'
        companion = 'research/owned-store/receipts/inputs.json.gz'
        payload = gzip.compress(b'[[1,2]]', mtime=1234)
        normalizer = normalize.Normalizer(Path('/new/checkout'))
        old = encoded({'original_inputs_sha256': normalize.digest(payload)})
        canonical = normalizer.receipt(path, old, {companion: payload})
        self.assertEqual({'original_inputs_sha256': normalize.digest(normalize.pack(b'[[1,2]]'))}, json.loads(canonical))
        stale = encoded({'original_inputs_sha256': 'stale-hash'})
        self.assertEqual('stale-hash', json.loads(normalizer.receipt(path, stale, {companion: payload}))['original_inputs_sha256'])
        self.assertEqual('semantic', normalize.classify(stale, old,
            normalizer.receipt(path, stale, {companion: payload}), canonical))

    def test_trust_paths_and_idempotence(self):
        root = Path('/scratch/worktree')
        normalizer = normalize.Normalizer(root, Path('/shared/.toolchain'), Path('/scratch/bend-lib'))
        paths = {'loaded_files': [
            {'path': '/shared/.toolchain/seed/./base.bend', 'sha256': 'keep-me'},
            {'path': '../../shared/.toolchain/seed/base.bend'},
            {'path': '../bend-lib/0xabc/bytes.bend'},
            {'path': '../../../.bend/lib/0xabc/bytes.bend'},
            {'path': '/Users/old/.bend/lib/0xabc/bytes.bend'}]}
        expected = ['.toolchain/seed/base.bend', '.toolchain/seed/base.bend',
                    '$BEND_LIB/0xabc/bytes.bend', '$BEND_LIB/0xabc/bytes.bend', '$BEND_LIB/0xabc/bytes.bend']
        got = normalizer.value(paths)
        self.assertEqual(expected, [p['path'] for p in got['loaded_files']])
        self.assertEqual('keep-me', got['loaded_files'][0]['sha256'])
        self.assertEqual(got, normalizer.value(got))

    def test_semantic_diff_points_to_missing_null_and_hash(self):
        self.assertEqual(['/inputs/src~1driver.bend', '/observation'], normalize.changed_fields(
            {'inputs': {'src/driver.bend': 'old'}, 'observation': None},
            {'inputs': {'src/driver.bend': 'new'}}))

    def test_unknown_dates_and_path_suffixes_remain_semantic(self):
        normalizer = normalize.Normalizer(Path('/checkout'))
        for value in ({'date': 'domain-date', 'budget_seconds': 7},
                      {'path': '/checkout-other/src/a', 'output': '/x/checkout/src/a'}):
            self.assertEqual(value, normalizer.value(value))


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'repo with spaces'
        self.root.mkdir()
        self.git('init', '-q')
        (self.root / '.gitignore').write_text('.local/\nnode_modules/\n.toolchain/\nignored/\n.env*\n!.env.example\n')
        for name in ('source.txt', 'deleted.txt', '.env.example', 'receipt.json'):
            (self.root / name).write_text('{}\n' if name.endswith('.json') else 'original')
        self.git('add', '.gitignore', 'source.txt', 'deleted.txt', '.env.example', 'receipt.json')
        (self.root / 'source.txt').write_text('working edit')
        (self.root / 'deleted.txt').unlink()
        (self.root / 'untracked.txt').write_text('untracked')
        (self.root / 'ignored').mkdir()
        (self.root / 'ignored/cache').write_text('ignored')
        (self.root / '.env').write_text('synthetic-test-secret')
        for name in ('.toolchain', 'node_modules'):
            (self.root / name).mkdir()

    def git(self, *args):
        return run.git(self.root, *args)

    def test_export_preserves_working_copy_and_never_reads_env(self):
        original = Path.read_bytes

        def guarded(path):
            if path.name.startswith('.env'):
                raise AssertionError('Attempt to read dotenv')
            return original(path)

        with patch.object(Path, 'read_bytes', guarded):
            manifest = run.export(self.root, self.base / 'scratch')
        scratch = self.base / 'scratch'
        self.assertEqual('working edit', (scratch / 'source.txt').read_text())
        self.assertEqual('untracked', (scratch / 'untracked.txt').read_text())
        self.assertIsNone(manifest['deleted.txt'])
        for name in ('deleted.txt', '.env', '.env.example', '.git', 'ignored'):
            self.assertFalse((scratch / name).exists(), name)
        self.assertTrue((scratch / '.toolchain').is_symlink())
        (scratch / 'source.txt').write_text('gate mutation')
        self.assertEqual('working edit', (self.root / 'source.txt').read_text())

    def test_internal_link_is_relocated_and_external_link_rejected(self):
        (self.root / 'alias').symlink_to(self.root / 'source.txt')
        run.export(self.root, self.base / 'good')
        self.assertEqual((self.base / 'good/source.txt').resolve(), (self.base / 'good/alias').resolve())
        (self.root / 'outside').symlink_to(self.base / 'external')
        with self.assertRaisesRegex(ValueError, 'External source symlink'):
            run.export(self.root, self.base / 'bad')

    def test_refresh_is_explicit_and_checks_snapshot(self):
        snapshot = run.export(self.root, self.base / 'scratch')
        normalized = self.base / 'normalized'
        normalized.mkdir()
        data = b'{"count": 2}\n'
        (normalized / 'receipt.json').write_bytes(data)
        receipts = [{'path': 'receipt.json', 'after_sha256': normalize.digest(data)}]
        with self.assertRaisesRegex(RuntimeError, 'every gate'):
            run.refresh(self.root, self.base, snapshot, receipts, False)
        (self.root / 'source.txt').write_text('concurrent edit')
        with self.assertRaisesRegex(RuntimeError, 'changed since export'):
            run.refresh(self.root, self.base, snapshot, receipts, True)
        (self.root / 'source.txt').write_text('working edit')
        (self.root / 'receipt.json').write_text('{"concurrent": true}')
        with self.assertRaisesRegex(RuntimeError, 'changed since export'):
            run.refresh(self.root, self.base, snapshot, receipts, True)
        (self.root / 'receipt.json').write_text('{}\n')
        self.assertEqual(['receipt.json'], run.refresh(self.root, self.base, snapshot, receipts, True))
        self.assertEqual(data, (self.root / 'receipt.json').read_bytes())

    def test_full_run_semantic_drift_is_read_only_and_repeatable(self):
        gate = run.Gate('probe', (sys.executable, '-c',
            'from pathlib import Path; Path("receipt.json").write_text(\'{"status":"pass","count":3}\\n\')'),
            ('receipt.json',))
        before = run.fingerprint(self.root, run.file_names(self.root))
        summaries = []
        old_cwd = Path.cwd()
        try:
            os.chdir(self.root)
            with patch.object(run, 'GATES', (gate,)), patch.dict(os.environ, {
                    'BEND_LIB': str(self.base / 'empty-lib'),
                    'TREE_SITTER_LANGUAGE_PACK_CACHE_DIR': str(self.base / 'empty-cache')}):
                for _ in range(2):
                    stdout = io.StringIO()
                    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
                        self.assertEqual(EXPECT['execution']['semantic_drift_exit'], run.main([]))
                    summaries.append(json.loads(stdout.getvalue()))
        finally:
            os.chdir(old_cwd)
        self.assertEqual(before, run.fingerprint(self.root, run.file_names(self.root)))
        self.assertEqual(summaries[0]['normalized'], summaries[1]['normalized'])
        self.assertEqual({'identical': 0, 'volatile-only': 0, 'semantic': 1}, summaries[0]['normalized']['receipt_counts'])
        for summary in summaries:
            self.assertFalse((Path(summary['run']['directory']) / 'worktree').exists())

    def test_failure_blocks_cli_refresh_and_does_not_reuse_old_receipt(self):
        gate = run.Gate('failure', (sys.executable, '-c', 'raise SystemExit(8)'), ('receipt.json',))
        old_cwd = Path.cwd()
        try:
            os.chdir(self.root)
            with patch.object(run, 'GATES', (gate,)), patch.dict(os.environ, {
                    'BEND_LIB': str(self.base / 'empty-lib'),
                    'TREE_SITTER_LANGUAGE_PACK_CACHE_DIR': str(self.base / 'empty-cache')}):
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(1, run.main(['--refresh']))
                summary = json.loads(stdout.getvalue())
        finally:
            os.chdir(old_cwd)
        self.assertEqual(8, summary['normalized']['gates'][0]['exit_code'])
        self.assertIsNone(summary['normalized']['receipts'][0]['after_sha256'])
        self.assertIn('every gate', summary['error'])
        self.assertEqual('{}\n', (self.root / 'receipt.json').read_text())

    def test_malformed_receipt_retains_process_evidence(self):
        gate = run.Gate('malformed', (sys.executable, '-c',
            'from pathlib import Path; Path("receipt.json").write_text("broken JSON")'), ('receipt.json',))
        old_cwd = Path.cwd()
        try:
            os.chdir(self.root)
            with patch.object(run, 'GATES', (gate,)), patch.dict(os.environ, {
                    'BEND_LIB': str(self.base / 'empty-lib'),
                    'TREE_SITTER_LANGUAGE_PACK_CACHE_DIR': str(self.base / 'empty-cache')}):
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(1, run.main([]))
                summary = json.loads(stdout.getvalue())
        finally:
            os.chdir(old_cwd)
        self.assertEqual('host-failure', summary['normalized']['gates'][0]['status'])
        self.assertEqual(0, summary['run']['gates'][0]['exit_code'])
        self.assertGreater(summary['run']['gates'][0]['seconds'], 0)


class ExecutionTests(unittest.TestCase):
    def test_failure_and_timeout_classifications(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = dict(os.environ, BEND_NO_TELEMETRY='1')
            for name, argv, expected in (
                ('nonzero', (sys.executable, '-c', 'raise SystemExit(7)'), 'failed'),
                ('missing', (str(root / 'absent'),), 'host-failure'),
                ('timeout', (sys.executable, '-c', 'import time; time.sleep(20)'), 'exhausted')):
                with self.subTest(name=name):
                    result = run.execute(run.Gate(name, argv), root, root, env, 0.1)
                    self.assertEqual(expected, result['status'])
                    self.assertEqual(7 if name == 'nonzero' else None, result['exit_code'])
            good = run.execute(run.Gate('lint', (sys.executable, '-c',
                'print("# pass 3\\nPASS: eight law rules;")')), root, root, env, 5)
            self.assertEqual('passed', good['status'])
            self.assertEqual({'tests': 3, 'law_rules': 8}, good['counts'])

    def test_dependency_order_parallelism_and_blocked_consumer(self):
        starts, ends = {}, {}
        overlap = threading.Barrier(2)
        gates = (run.Gate('producer', ()), run.Gate('independent', ()),
                 run.Gate('consumer', (), needs=('producer',)), run.Gate('failure', ()),
                 run.Gate('blocked', (), needs=('failure',)))

        def worker(gate):
            starts[gate.name] = time.monotonic()
            if gate.name in ('producer', 'independent'):
                overlap.wait(timeout=5)
            ends[gate.name] = time.monotonic()
            return {'name': gate.name, 'status': 'failed' if gate.name == 'failure' else 'passed', 'seconds': 0.03}

        got = run.schedule(gates, worker, 2)
        self.assertLess(starts['independent'], ends['producer'])
        self.assertGreaterEqual(starts['consumer'], ends['producer'])
        self.assertNotIn('blocked', starts)
        self.assertEqual('blocked', got[-1]['status'])

    def test_all_registered_gates_and_required_edges(self):
        names = [g.name for g in run.GATES]
        self.assertEqual(len(names), len(set(names)))
        self.assertLessEqual({'frontend', 'checker', 'structural', 'fields', 'wasm', 'wasm-trust',
                              'fields-trust', 'structural-trust', 'owned-store', 'flat-store',
                              'recursion', 'fields-wasm', 'census', 'lint:verify', 'perch-context'}, set(names))
        self.assertEqual({'wasm-trust': ('wasm',), 'fields-trust': ('fields',),
                          'structural-trust': ('structural',), 'flat-store': ('owned-store',)},
                         {g.name: g.needs for g in run.GATES if g.needs})

    def test_nonzero_lint_without_completion_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            got = run.execute(run.Gate('lint', (sys.executable, '-c', 'print("# pass 3")')),
                              root, root, dict(os.environ), 5)
            self.assertEqual('host-failure', got['status'])


class SemanticMutantTests(unittest.TestCase):
    def test_parseable_mutants_are_killed_by_unchanged_literal_expectations(self):
        source = (HERE / 'normalize.py').read_text()
        mutants = (
            ('ignore-hash', 'result[name] = visit(child, (*at, key))',
             "result[name] = {} if key == 'inputs' else visit(child, (*at, key))", 'source-hash'),
            ('sort-observations', 'return [visit(child, (*at, str(i))) for i, child in enumerate(item)]',
             'return sorted([visit(child, (*at, str(i))) for i, child in enumerate(item)])', 'array-order'),
            ('ignore-observation', 'result[name] = visit(child, (*at, key))',
             "result[name] = '' if key == 'stdout' else visit(child, (*at, key))", 'observation'),
            ('erase-budget', 'result[name] = visit(child, (*at, key))',
             "result[name] = 0 if key == 'budget_seconds' else visit(child, (*at, key))", 'budget'),
        )
        for name, old, new, witness in mutants:
            with self.subTest(mutant=name):
                self.assertEqual(1, source.count(old))
                namespace = {'__name__': 'mutant'}
                exec(compile(source.replace(old, new), name, 'exec'), namespace)
                normalizer = namespace['Normalizer'](Path('/new/checkout'))
                case = next(c for c in EXPECT['receipt_cases'] if c['name'] == witness)
                before, after = encoded(case['before']), encoded(case['after'])
                got = namespace['classify'](before, after,
                    normalizer.receipt('gate.json', before, {}), normalizer.receipt('gate.json', after, {}))
                self.assertNotEqual(case['expected'], got, f'Surviving semantic mutant: {name}')

    def test_exit_and_dependency_mutants_run_but_violate_controls(self):
        source = (HERE / 'run.py').read_text()

        def module(name, old, new):
            self.assertEqual(1, source.count(old))
            loaded = types.ModuleType(name)
            with patch.dict(sys.modules, {name: loaded}):
                exec(compile(source.replace(old, new), name, 'exec'), loaded.__dict__)
            return loaded

        mutant = module('swallowed_exit', "'passed' if result['exit_code'] == 0 else 'failed'", "'passed'")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gate = run.Gate('probe', (sys.executable, '-c',
                'print("# pass 3\\nPASS: eight law rules;"); raise SystemExit(7)'))
            control = run.execute(gate, root, root, dict(os.environ), 5)
            broken = mutant.execute(gate, root, root, dict(os.environ), 5)
            self.assertEqual('failed', control['status'])
            self.assertEqual('passed', broken['status'])
            self.assertEqual(7, broken['exit_code'])

        mutant = module('discarded_dependency', 'pending, running, done = list(gates), {}, {}',
                        'pending, running, done = [Gate(g.name, g.argv, g.outputs) for g in gates], {}, {}')
        gates = (run.Gate('producer', ()), run.Gate('consumer', (), needs=('producer',)))

        def worker(gate):
            return {'name': gate.name, 'status': 'failed' if gate.name == 'producer' else 'passed', 'seconds': 0}

        with contextlib.redirect_stderr(io.StringIO()):
            control = run.schedule(gates, worker, 2)
            broken = mutant.schedule(gates, worker, 2)
        self.assertEqual('blocked', control[1]['status'])
        self.assertEqual('passed', broken[1]['status'])


if __name__ == '__main__':
    unittest.main()

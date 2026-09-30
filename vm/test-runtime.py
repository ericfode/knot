#!/usr/bin/env python3
"""Controls relocated with the VM-owned runtime preflight."""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('vm_gates', ROOT / 'vm/run-gates.py')
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        scratch = ROOT / '.local/vm-model/runtime-tests'
        scratch.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        pin = self.root / 'tests/compiler-io/expectations.json'
        pin.parent.mkdir(parents=True)
        pin.write_text('{"seed":{"bun":"1.3.14"}}')
        self.binary = self.root / 'bun'
        self.env = {'PATH': str(self.root), 'BEND_NO_TELEMETRY': '1'}

    def test_runtime_guard_uses_the_frozen_pin_and_selected_path(self):
        for version, status in (('1.3.14', 0), ('1.3.11', 0), ('1.3.14', 1)):
            with self.subTest(version=version, status=status):
                self.binary.write_text(f'#!/bin/sh\necho {version}\nexit {status}\n')
                self.binary.chmod(0o755)
                if version == '1.3.14' and status == 0:
                    self.assertEqual({'bun': {'version': '1.3.14', 'executable': str(self.binary)}},
                                     run.check_runtime(self.root, self.env))
                else:
                    with self.assertRaisesRegex(RuntimeError, 'io-host requires 1.3.14'):
                        run.check_runtime(self.root, self.env)
        self.binary.unlink()
        with self.assertRaisesRegex(RuntimeError, 'Bun is missing from PATH'):
            run.check_runtime(self.root, self.env)

    def test_runtime_mismatch_stops_before_scheduling_or_receipt_removal(self):
        self.binary.write_text('#!/bin/sh\necho 1.3.11\n')
        self.binary.chmod(0o755)
        (self.root / 'receipt.json').write_text('{}\n')
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        with patch.object(run, 'ROOT', self.root), patch.dict(os.environ, self.env), \
             patch.object(run.subprocess, 'run', wraps=subprocess.run) as execute:
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(1, run.main([]))
            self.assertIn('io-host requires 1.3.14', stderr.getvalue())
            self.assertEqual(1, execute.call_count)
            self.assertEqual([str(self.binary), '--version'], execute.call_args.args[0])
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_pinned_runtime_forwards_arguments_environment_and_exit(self):
        with patch.object(run, 'ROOT', self.root), patch.object(run, 'check_runtime') as check, \
             patch.object(run.subprocess, 'run', return_value=subprocess.CompletedProcess([], 3)) as execute:
            self.assertEqual(3, run.main(['--jobs', '2']))
            env = execute.call_args.kwargs['env']
            check.assert_called_once_with(self.root, env)
            self.assertEqual('1', env['BEND_NO_TELEMETRY'])
            execute.assert_called_once_with(['npm', 'run', '-s', 'gates', '--', '--jobs', '2'],
                                            cwd=self.root, env=env)


if __name__ == '__main__':
    unittest.main()

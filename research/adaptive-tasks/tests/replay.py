#!/usr/bin/env python3
"""Exercise replay destinations without changing retained evidence."""
from hashlib import sha256
from pathlib import Path
import json
import os
import subprocess
import tempfile
import unittest

HERE=Path(__file__).resolve().parents[1]
ROOT=HERE.parents[1]
RETAINED=['receipts/checks.json','receipts/gpu.json','codegen/receipt.json',
          'codegen/conformance.c','codegen/conformance.js',
          'codegen/conformance.stdout','codegen/cpu_frames.records.json']


def retained():
    return {name:sha256((HERE/name).read_bytes()).hexdigest() for name in RETAINED}


class Replay(unittest.TestCase):
    def setUp(self):
        self.before=retained()

    def tearDown(self):
        self.assertEqual(retained(),self.before,'replay changed retained evidence')

    def command(self,args,success=True):
        result=subprocess.run([str(x) for x in args],cwd=ROOT,capture_output=True,text=True,
                              timeout=120,env={**os.environ,'BEND_NO_TELEMETRY':'1'})
        if success:self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        else:self.assertNotEqual(result.returncode,0,result.stdout+result.stderr)
        return result

    def test_cpu_default_replay(self):
        self.command(['python3',HERE/'check.py','--cpu-only'])
        report=json.loads((ROOT/'.local/adaptive-tasks/replay/cpu-checks.json').read_text())
        self.assertEqual(report['status'],'cpu-only')
        self.assertEqual(len(report['fixtures']),10)
        self.assertEqual(len(report['negative_quantity']),2)
        self.assertEqual(len(report['mutants']),5)

    def test_cpu_selected_output(self):
        with tempfile.TemporaryDirectory(prefix='knot-adaptive-replay-') as folder:
            self.command(['python3',HERE/'check.py','--cpu-only','--out-dir',folder])
            self.assertEqual(json.loads((Path(folder)/'cpu-checks.json').read_text())['status'],'cpu-only')

    def test_codegen_default_replay(self):
        self.command(['python3',HERE/'codegen/generate.py'])
        report=json.loads((ROOT/'.local/adaptive-tasks/codegen/receipt.json').read_text())
        self.assertEqual(report['status'],'pass')
        self.assertEqual(report['seed_execution']['stdout'],report['native_execution']['stdout'])
        self.assertEqual(report['seed_execution']['stdout'],report['js_execution']['stdout'])

    def test_codegen_selected_output(self):
        with tempfile.TemporaryDirectory(prefix='knot-codegen-replay-') as folder:
            self.command(['python3',HERE/'codegen/generate.py','--out-dir',folder])
            self.assertEqual(json.loads((Path(folder)/'receipt.json').read_text())['status'],'pass')

    def test_cpu_only_cannot_replace_complete_evidence(self):
        result=self.command(['python3',HERE/'check.py','--cpu-only','--update-receipts'],success=False)
        self.assertIn('cannot replace a complete historical receipt',result.stderr)

    def test_output_modes_are_exclusive(self):
        commands=[['python3',HERE/'check.py'],['python3',HERE/'codegen/generate.py'],
                  ['node',HERE/'gpu/check.mjs']]
        for command in commands:
            with self.subTest(command=command):
                result=self.command(command+['--out-dir','.local/adaptive-tasks/conflict','--update-receipts'],success=False)
                self.assertIn('--out-dir',result.stderr)


if __name__=='__main__':unittest.main(verbosity=2)

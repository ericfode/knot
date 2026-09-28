#!/usr/bin/env python3
"""Offline context controls, semantic mutants and complete compiler preflight."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
EXPECT = json.loads((HERE / 'expectations.json').read_text())
TESTS = ('tests/perch-context.test.mjs', 'tests/perch-context-integration.test.mjs',
         'tests/perch-context-mutants.test.mjs')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv):
    result = subprocess.run(argv, cwd=ROOT, env={**os.environ, 'BEND_NO_TELEMETRY': '1'},
                            text=True, capture_output=True, timeout=120)
    if result.returncode:
        raise RuntimeError(f'{argv}: exit {result.returncode}\n{result.stdout}\n{result.stderr}')
    return result.stdout


def main():
    assert digest(ROOT / 'perch-style.json') == EXPECT['rubric_sha256'], 'Rubric identity changed'
    output = run(['node', '--test', *TESTS])
    names = re.findall(r'^# Subtest: (.+)$', output, re.M)
    mutants = [name.removeprefix('semantic mutant killed: ') for name in names
               if name.startswith('semantic mutant killed: ')]
    fixtures = [name for name in names if not name.startswith('semantic mutant killed: ')]
    assert mutants == EXPECT['mutants'], mutants
    assert len(fixtures) == EXPECT['controls'], fixtures
    assert re.search(r'^# fail 0$', output, re.M), output
    assert re.search(rf"^# pass {len(names)}$", output, re.M), output
    scratch = ROOT / '.local/perch-context'
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='preflight-', dir=scratch) as temp:
        receipt = Path(temp) / 'preflight.json.gz'
        store = Path(os.environ.get('BEND_LIB', str(Path.home() / '.bend/lib'))).resolve()
        run(['node', 'scripts/perch-style.mjs', '--preflight',
             '--manifest=docs/compiler-campaign/manifest.json', f'--package-store={store}', f'--output={receipt}'])
        report = json.loads(gzip.decompress(receipt.read_bytes()))
    groups = report['groups']
    inventory = json.loads(run(['node', '--input-type=module', '-e', '''
import { readFile, readdir } from 'node:fs/promises';
import { analyzeBendSource } from './scripts/perch-bend.mjs';
const expected = [];
for (const file of (await readdir('src')).filter(f => f.endsWith('.bend')).sort()) {
  const path = 'src/' + file, parsed = await analyzeBendSource(await readFile(path, 'utf8'));
  if (parsed.parser_status !== 'parsed') throw new Error(path + ' does not parse');
  for (const d of [...parsed.declarations, ...parsed.datatype_declarations]) expected.push(path + '::' + (d.qualified_name ?? d.name));
}
console.log(JSON.stringify(expected.sort()));
''']))
    covered = {u['target'] for g in groups for u in g['units']}
    actual = {
        'unavailable_compositions': sum(not g['composition']['available'] for g in groups),
        'over_bound_groups': sum(g['composition']['source_bytes'] > EXPECT['composition_byte_limit'] for g in groups),
        'unresolved_composition_references': sum(len(g['composition']['unresolved']) for g in groups),
        'truncated_declarations': report['summary']['truncated_units'],
        'uncovered_declarations': len(set(inventory) - covered),
        'provider_requests': report['provider_requests'],
    }
    assert covered == set(inventory), 'Preflight must cover exactly every current compiler declaration'
    assert actual == EXPECT['compiler_preflight'], actual
    inputs = (*TESTS, 'tests/perch-context/CONTRACT.md', 'tests/perch-context/expectations.json',
              'tests/perch-context/check.py', 'scripts/perch-style.mjs', 'scripts/perch-bend-context.mjs',
              'scripts/perch-context-interfaces.mjs', 'docs/compiler-campaign/manifest.json', 'perch-style.json')
    record = {'status': 'pass', 'context_policy': EXPECT['context_policy'],
              'fixtures': fixtures, 'mutants': mutants, 'tests': len(names), 'compiler_preflight': actual,
              'summary': report['summary'], 'distinct_declarations': len({u['target'] for g in groups for u in g['units']}),
              'groups': [{'name': g['name'], 'summary': g['summary'], 'composition': g['composition']} for g in groups],
              'inputs': {p: digest(ROOT / p) for p in inputs}}
    path = HERE / 'receipts/context.json'
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + '\n')
    print(f"PASS: {len(fixtures)} context controls; {len(mutants)} semantic mutants killed; "
          f"{len(groups)} compositions; {record['distinct_declarations']} distinct declarations; 0 blockers; 0 provider requests")


if __name__ == '__main__':
    main()

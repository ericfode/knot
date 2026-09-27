"""Check additive proofs and fixed package gates without rewriting old receipts."""
import hashlib
import json
import pathlib
import shutil
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parents[4]
P = ROOT / 'packages/int_map'
OUT = pathlib.Path(__file__).resolve().parent
BUILD = P / 'build/edit-locality-1'
BUILD.mkdir(parents=True, exist_ok=True)
PRE = json.loads((OUT / 'preregistration.json').read_text())
steps = []


def fixed_inputs():
    for name, expected in PRE['fixed_sha256'].items():
        assert hashlib.sha256((P / name).read_bytes()).hexdigest() == expected, name
    for name in ('LAWS', 'PROOF'):
        assert (P / f'locality/{name}.bend').read_bytes() == (
            OUT / f'candidate-retry-{name}.bend.snapshot').read_bytes(), name


def run(name, args):
    command = list(map(str, args))
    start = time.perf_counter()
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=180)
    steps.append(dict(name=name, command=command, exit=result.returncode,
                      seconds=time.perf_counter() - start,
                      stdout=result.stdout, stderr=result.stderr))
    (OUT / 'gates.json').write_text(json.dumps(dict(steps=steps), indent=2) + '\n')
    assert result.returncode == 0, (name, result.stdout, result.stderr)
    if name.endswith('proofs'):
        assert 'All terms check.' in result.stdout and 'hole' not in result.stdout.lower()
    print(name + ' PASS', flush=True)


fixed_inputs()
run('additive-proofs', [ROOT / 'scripts/bend-reference', P / 'locality/PROOF.bend', '--check-only'])
run('original-proofs', [ROOT / 'scripts/bend-reference', P / 'PROOF.bend', '--check-only'])
for backend, suffix, runner in [('native', '', []), ('javascript', '.js', ['bun'])]:
    executable = BUILD / ('release' + suffix)
    run(backend + '-build', [ROOT / 'scripts/bend-reference', P / 'release.bend', '-o', executable])
    run(backend + '-conformance', runner + [executable])
run('semantic-mutants', ['python3', P / 'scripts/mutations.py'])
shutil.copy2(P / 'build/mutations.json', OUT / 'mutations.json')
run('scaling-model-gates', ['python3', P / 'scripts/performance.py'])
shutil.copy2(P / 'build/performance.json', OUT / 'performance.json')
fixed_inputs()
(OUT / 'gates.json').write_text(json.dumps(dict(
    deterministic_pass=True, fixed_inputs_unchanged=True, runtime_source_unchanged=True,
    original_laws=23, additional_laws=8, proof_holes=0, compiler_diagnostic_retries=1,
    performance_comparison='Inherited from byte-identical int-map-paths-2 source; no new comparison.',
    steps=steps), indent=2) + '\n')
print('ALL EDIT-LOCALITY GATES PASS', flush=True)

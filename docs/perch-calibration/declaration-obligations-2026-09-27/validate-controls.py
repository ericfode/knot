"""Fixed literal observations for fresh calibration controls, not a package gate."""
import hashlib
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BEND = pathlib.Path(sys.argv[1]).resolve()
BUILD = ROOT / '.local/perch-declaration-obligations'
BUILD.mkdir(parents=True, exist_ok=True)
CASES = [('Nil{}', 0), ('[1]', 1), ('[1,2]', 33), ('[1,2,3]', 1026),
         ('[4294967295,1]', 4294967266), ('[0,1,0]', 31), ('[5,5]', 160)]
expected = ''.join(f'{value}\n' for _, value in CASES)
rows = []
for specimen in ['a', 'b']:
    source = (HERE / 'controls' / f'{specimen}.bend').read_text()
    program = source + '\ndef main() -> IO(Unit):\n  do IO<Unit>:\n' + ''.join(
        f'    IO.print(U32.show(Fingerprint.of({literal})))\n' for literal, _ in CASES)
    path = BUILD / f'{specimen}.bend'
    path.write_text(program)
    commands = [[str(BEND), str(path), '--check-only']]
    for backend, suffix, runner in [('native', '', []), ('javascript', '.js', ['bun'])]:
        output = BUILD / f'{specimen}{suffix}'
        commands += [[str(BEND), str(path), '-o', str(output)], runner + [str(output)]]
    receipts = []
    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True)
        is_observation = command[0] != str(BEND)
        receipts.append({'argv': command, 'exit': result.returncode,
                         'stdout': result.stdout, 'stderr': result.stderr,
                         'is_observation': is_observation})
        assert result.returncode == 0, receipts[-1]
        if is_observation:
            assert result.stdout == expected, receipts[-1]
    rows.append({'specimen': specimen, 'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
                 'commands': receipts})
record = {'status': 'passed', 'literal_observations_per_backend': len(CASES),
          'cases': [{'input': x, 'expected_u32': y} for x, y in CASES], 'rows': rows,
          'scope': 'Finite independent literal observations; no universal equivalence proof.'}
with (HERE / 'control-gates.json').open('x') as f:
    json.dump(record, f, indent=2)
    f.write('\n')
print('Both controls check and match all seven fixed observations on native and Bun.')

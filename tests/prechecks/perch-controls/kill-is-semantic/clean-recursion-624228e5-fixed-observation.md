<!-- prechecks packet v1; rule=kill-is-semantic; increment=recursion; head=624228e56d8b; base=185b7d5ffad5; builder=scripts/prechecks/packets@3a2ef420dff1; sources: tests/compiler-recursion/check.py@624228e5 sha256=0c5a3355ed138e9c14bb6043777e19542e8beef9ca03becd137e3b0bd6438f30 -->
# Claim
Statements about what counts as a kill:

- tests/compiler-recursion/README.md: All three mutants typecheck with the seed and are killed by fixed observations: admitting every self-call incorrectly checks `same-parameter`; suppressing field propagation rejects `direct`; suppressing nested propagation rejects `even`.
- tests/compiler-recursion/README.md: The latter two report `Unsupported check recursive-call`, as required for a semantic kill.
- tests/compiler-recursion/README.md: No crash, missing import or timeout counts as a kill.
- tests/compiler-recursion/SPEC.md: Crashes and timeouts are not semantic kills.

# Evidence
`tests/compiler-recursion/check.py:80-186` function `main`:
```python
   80  def main():
   81      parser = argparse.ArgumentParser()
   82      parser.add_argument('--reference-only', action='store_true')
   83      args = parser.parse_args()
   84      BUILD.mkdir(parents=True, exist_ok=True)
   85      RECEIPTS.mkdir(parents=True, exist_ok=True)
   86      manifest = json.loads((HERE / 'cases.json').read_text())
   87      fixtures = sorted((HERE / 'fixtures').glob('*.bend'))
   88      require({str(p.relative_to(HERE)) for p in fixtures} ==
   89              {c['file'] for c in manifest['cases']}, 'Fixture manifest mismatch')
   90      fixed = {str(p.relative_to(ROOT)): digest(p) for p in fixtures + [HERE / 'cases.json']}
   91      if args.reference_only:
   92          receipt = RECEIPTS / 'reference.json'
   93          require(not receipt.exists(), 'The preimplementation expectation freeze is immutable')
   94          result = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
   95                    'seed_revision': manifest['seed_revision'], 'status': 'passed',
   96                    'frozen_inputs': fixed,
   97                    'baseline_implementation': {str(p.relative_to(ROOT)): digest(p)
   98                        for p in sorted((ROOT / 'src').glob('*.bend'))},
   99                    'observations': reference(manifest)}
  100          receipt.write_text(json.dumps(result, indent=2) + '\n')
  101          print(f"Reference freeze passed: {len(result['observations'])} fixtures; {receipt}")
  102          return
  103      frozen = json.loads((RECEIPTS / 'reference.json').read_text())
  104      require(frozen['status'] == 'passed' and frozen['frozen_inputs'] == fixed,
  105              'Expectations changed since the preimplementation seed freeze')
  106      paths = sorted((ROOT / 'src').glob('*.bend')) + fixtures + [Path(__file__), HERE / 'cases.json',
  107          ROOT / 'src/SPEC.md', ROOT / 'src/CONTRACT.json', HERE / 'SPEC.md']
  108      record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'incomplete',
  109                'seed_revision': manifest['seed_revision'],
  110                'inputs': {str(p.relative_to(ROOT)): digest(p) for p in paths},
  111                'seed_inputs': {str(p.relative_to(ROOT)): digest(p) for p in
  112                    sorted((ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2').glob('*.ts')) +
  113                    [ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2/base.bend']},
  114                'expectation_freeze_sha256': digest(RECEIPTS / 'reference.json')}
  115      try:
  116          record['tools'] = {t: successful([t, '--version'])['stdout'].strip() for t in ('bun', 'node', 'python3')}
  117          record['proof'] = successful([*SEED, ROOT / 'src/recursion-PROOF.bend'])
  118          require(record['proof']['stdout'].strip() == 'All terms check.', record['proof'])
  119          record['reference'] = reference(manifest)
  120          record['builds'], lanes = [], {}
  121          for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
  122              lanes[lane] = {}
  123              for phase in ('check', 'eval', 'compile'):
  124                  output = BUILD / (phase + suffix)
  125                  built = successful([*SEED, ROOT / f'src/{phase}-cli.bend', '-o', output])
  126                  record['builds'].append({'lane': lane, 'phase': phase, 'result': built, 'sha256': digest(output)})
  127                  lanes[lane][phase] = [*runtime, output]
  128          record['fixtures'] = []
  129          for case in manifest['cases']:
  130              item = {'case': case['name'], 'lanes': {}}
  131              for lane, commands in lanes.items():
  132                  path = HERE / case['file']
  133                  checked = run([*commands['check'], path]); observe(checked, case['check'])
  134                  evaluated = run([*commands['eval'], path, 'main', 65536]); observe(evaluated, case['eval'])
  135                  output = BUILD / (case['name'] + '-' + lane + '.wasm')
  136                  marker = b'existing artifact: recursive programs remain unemitted\n'
  137                  output.write_bytes(marker)
  138                  compiled = run([*commands['compile'], path, output]); observe(compiled, case['compile'])
  139                  require(output.read_bytes() == marker, ('artifact changed', compiled))
  140                  item['lanes'][lane] = {'check': checked, 'eval': evaluated,
  141                      'compile': compiled, 'artifact_preserved': True}
  142              record['fixtures'].append(item)
  143          cases = {c['name']: c for c in manifest['cases']}
  144          record['fuel'] = []
  145          for lane, commands in lanes.items():
  146              for probe in manifest['fuel']:
  147                  result = run([*commands['eval'], HERE / cases[probe['case']]['file'], 'main', probe['budget']])
  148                  observe(result, probe['expected'])
  149                  record['fuel'].append({'lane': lane, 'case': probe['case'], 'result': result})
  150          record['mutants'] = []
  151          for name, file, old, new, witness, exit_code in MUTANTS:
  152              directory = BUILD / name; directory.mkdir(exist_ok=True)
  153              for source in (ROOT / 'src').glob('*.bend'):
  154                  shutil.copy2(source, directory / source.name)
  155              target = directory / file; source = target.read_text()
  156              require(source.count(old) == 1, (name, 'mutation must be unique'))
  157              target.write_text(source.replace(old, new))
  158              entry = directory / 'check-cli.bend'
  159              typecheck = successful([*SEED, entry, '--check-only'])
  160              require(typecheck['stdout'].strip() == 'All terms check.', typecheck)
  161              output = directory / 'mutant.js'; built = successful([*SEED, entry, '-o', output])
  162              actual = run(['bun', output, HERE / cases[witness]['file']])
  163              # Require the intended semantic observation, never a crash or timeout.
  164              observe(actual, {'exit': 0, 'contains': 'Checked\n'} if exit_code == 0 else
  165                      {'exit': 3, 'diagnostic': 'Unsupported\tcheck\trecursive-call\t'})
  166              try:
  167                  observe(actual, cases[witness]['check'])
  168              except AssertionError:
  169                  killed = True
  170              else:
  171                  killed = False
  172              require(killed, (name, 'survived'))
  173              record['mutants'].append({'name': name, 'file': file, 'old': old, 'new': new,
  174                  'sha256': digest(target), 'typecheck': typecheck, 'build': built,
  175                  'witness': witness, 'expected': cases[witness]['check'], 'actual': actual,
  176                  'outcome': 'semantic-kill'})
  177          require(all(digest(ROOT / p) == h for p, h in record['inputs'].items()), 'Inputs changed during gate')
  178          record['status'] = 'passed'
  179      except Exception as e:
  180          record['failure'] = repr(e)
  181          raise
  182      finally:
  183          (RECEIPTS / 'recursion.json').write_text(json.dumps(record, indent=2) + '\n')
  184      print(f"Recursion gate passed: {len(record['reference'])} seed fixtures, "
  185            f"{6*len(record['fixtures'])} native/Bun phase observations, "
  186            f"{len(record['fuel'])} fuel probes, {len(record['mutants'])} semantic mutants")
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

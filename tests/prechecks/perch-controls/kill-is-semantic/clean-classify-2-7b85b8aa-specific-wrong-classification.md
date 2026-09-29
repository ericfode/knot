<!-- prechecks packet v1; rule=kill-is-semantic; increment=classify-2; head=7b85b8aa7882; base=fa31fec064ba; builder=scripts/prechecks/packets@3a2ef420dff1; sources: tests/compiler-classification/check.py@7b85b8aa sha256=5c20ea02a6a3a075af56ee6df9a8830c3585692be140147084b9194b483030c8 -->
# Claim
Statements about what counts as a kill:

- tests/compiler-classification/README.md: It replays all 17 exact seed outputs and parser observations and kills six parseable, type-correct semantic mutants: re-enable non-leading templates, recognize equality as binding, recognize arrow as binding, and misclassify each of the three type application positions as Invalid.
- tests/compiler-classification/README.md: Every kill requires the specific wrong classification and unchanged source location; build failures, timeouts and host failures cannot count as kills.
- tests/compiler-classification/REPORT.md: | Gate | Exact passed coverage | | --- | --- | | frontend | 14 original seed fixtures; 28 parser observations; 24 boundaries; 4 original mutants; 29 classification fixtures; 58 classification parser observations; 7 classification mutants; 174 downstream rejections, including 58 preserved compiler outputs | | checker | 49 seed fixtures; 98 checked observations; 10 depth probes; 16 catalog-bound observations in 2 records; 7 mutants | | structural | 16 seed fixtures; 64 catalog/compiler observations; 4 boundary pairs; 7 mutants | | fields | 40 seed fixtures; 240 phase observations; 36 budget probes; 6 host probes; 12 level/inspection observations in 2 records; 9 mutants | | wasm | 25 programs; 90 seed calls in 2 execution lanes; 64 rejection pairs; 44 boundaries; 7 mutants | | wasm-trust | 3 entries; 0 proof holes | | fields-trust | 4 entries; 0 proof holes | | structural-trust | 2 entries; 0 proof holes | | owned-store | 3,532 cases in each of 2 lanes; 15 literal witnesses; 6 mutants | | flat-store | 13,621 observations, 3,534 instances, 2 installed boundary states and 7 lifecycle checks per lane; 2 lanes; 9 mutants | | recursion | 19 seed fixtures; 114 phase observations; 4 fuel probes; 3 mutants | | fields-wasm | 8 fixtures; 32 seed calls; 64 evaluator and 64 Node observations; 50 frozen enum-byte checks; 30 boundary probes; 4 mutants killed in both lanes; 5 checked laws | | census | 30 compiler source files; 437 declaration events; 41 feature classes | | lint:verify | 127 tests; 8 law-rule wiring controls; 0 provider calls | | classification | 17 exact frozen seed outputs; 17 parser observations; 6 type-correct semantic mutants; 16 filled frontend laws |
- tests/compiler-classification/REPORT.md: | Gate | Exact passed coverage | | --- | --- | | frontend | 14 original seed fixtures; 28 parser observations; 24 boundaries; 4 original mutants; 29 classification fixtures; 58 classification parser observations; 7 classification mutants; 174 downstream rejections, including 58 preserved compiler outputs | | checker | 49 seed fixtures; 98 checked observations; 10 depth probes; 16 catalog-bound observations in 2 records; 7 mutants | | structural | 16 seed fixtures; 64 catalog/compiler observations; 4 boundary pairs; 7 mutants | | fields | 40 seed fixtures; 240 phase observations; 36 budget probes; 6 host probes; 12 level/inspection observations in 2 records; 9 mutants | | wasm | 25 programs; 90 seed calls in 2 execution lanes; 64 rejection pairs; 44 boundaries; 7 mutants | | wasm-trust | 3 entries; 0 proof holes | | fields-trust | 4 entries; 0 proof holes | | structural-trust | 2 entries; 0 proof holes | | owned-store | 3,532 cases in each of 2 lanes; 15 literal witnesses; 6 mutants | | flat-store | 13,621 observations, 3,534 instances, 2 installed boundary states and 7 lifecycle checks per lane; 2 lanes; 9 mutants | | recursion | 19 seed fixtures; 114 phase observations; 4 fuel probes; 3 mutants | | fields-wasm | 8 fixtures; 32 seed calls; 64 evaluator and 64 Node observations; 50 frozen enum-byte checks; 30 boundary probes; 4 mutants killed in both lanes; 5 checked laws | | census | 30 compiler source files; 437 declaration events; 41 feature classes | | lint:verify | 127 tests; 8 law-rule wiring controls; 0 provider calls | | classification | 17 exact frozen seed outputs; 17 parser observations; 6 type-correct semantic mutants; 16 filled frontend laws | `npm run -s gates:verify` exited **0**: **18 tests**, including the wrapper's six semantic mutants.

# Evidence
`tests/compiler-classification/check.py:21-108` function `main`:
```python
   21  def main():
   22      BUILD.mkdir(parents=True, exist_ok=True)
   23      RECEIPT.parent.mkdir(parents=True, exist_ok=True)
   24      cases = [c for c in json.loads(MANIFEST.read_text())['cases']
   25               if c.get('increment') == 'classify-2']
   26      require(len(cases) == 17, 'The frozen classify-2 controls must remain complete')
   27      seed = ['bun', '.toolchain/bend-2.0.29-574b6d3/bend2/main.ts']
   28      sources = sorted((ROOT / 'src').glob('*.bend'))
   29      inputs = sources + [MANIFEST, Path(__file__), ROOT / 'tests/subsets/check_frontend.py']
   30      inputs += [ROOT / 'tests/subsets' / c['file'] for c in cases]
   31      record = {
   32          'date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
   33          'status': 'incomplete',
   34          'scope': 'Parser classification precision; no new executable language capability',
   35          'seed_revision': json.loads(MANIFEST.read_text())['seed_revision'],
   36          'inputs': {str(p.relative_to(ROOT)): digest(p) for p in inputs},
   37          'fixtures': [], 'mutants': [],
   38      }
   39      try:
   40          record['proof'] = successful([*seed, 'src/PROOF.bend'])
   41          require(record['proof']['stdout'].strip() == 'All terms check.', record['proof'])
   42          output = BUILD / 'parse.js'
   43          record['build'] = successful([*seed, 'src/parse-cli.bend', '-o', output])
   44          record['generated_sha256'] = digest(output)
   45          for case in cases:
   46              path = ROOT / 'tests/subsets' / case['file']
   47              require(digest(path) == case['sha256'], f"Frozen fixture changed: {case['file']}")
   48              expected = case['reference']
   49              require(expected['command'] == [*seed, str(path.relative_to(ROOT))], expected)
   50              reference = run(expected['command'])
   51              require(reference['exit'] == expected['exit'], reference)
   52              for stream in ('stdout', 'stderr'):
   53                  require(reference[stream].replace(str(ROOT), '$ROOT') == expected[stream], reference)
   54              actual = run(['bun', output, path])
   55              classified(actual, case['knot'])
   56              record['fixtures'].append({'file': case['file'], 'reference': reference,
   57                                         'expected': case['knot'], 'lanes': {'bun': actual}})
   58  
   59          # Each mutant changes an outcome, not syntax, typing, budgets, or tests.
   60          mutations = [
   61              ('nonleading-template', 'Bool.and(parameters,starts(t,"~"))', 'False{}',
   62               'template-nonleading', 'Unsupported\tparse\ttemplate-binder'),
   63              ('equality-as-binding', 'Bool.or(starts(tail,"="),starts(tail,">"))',
   64               'starts(tail,">")', 'destructure-equality', 'Unsupported\tparse\tdestructuring-binding'),
   65              ('arrow-as-binding', 'Bool.or(starts(tail,"="),starts(tail,">"))',
   66               'starts(tail,"=")', 'destructure-arrow', 'Unsupported\tparse\tdestructuring-binding'),
   67              ('parameter-application-invalid', 'unsupported(rest,"parameter-type")',
   68               'invalid(rest,"parameter-type")', 'application-parameter', 'Invalid\tparse\tparameter-type'),
   69              ('return-application-invalid', 'unsupported(Con{colon,body},"type-application")',
   70               'invalid(Con{colon,body},"type-application")', 'application-return', 'Invalid\tparse\ttype-application'),
   71              ('binding-application-invalid', 'unsupported(tail,"type-application")',
   72               'invalid(tail,"type-application")', 'application-binding', 'Invalid\tparse\ttype-application'),
   73          ]
   74          for name, before, after, witness, wrong in mutations:
   75              directory = BUILD / name
   76              directory.mkdir(exist_ok=True)
   77              for source in sources:
   78                  shutil.copyfile(source, directory / source.name)
   79              target = directory / 'parse.bend'
   80              source = target.read_text()
   81              require(source.count(before) == 1, f'Mutation anchor: {name}')
   82              target.write_text(source.replace(before, after))
   83              checked = successful([*seed, directory / 'parse-cli.bend', '--check-only'])
   84              require(checked['stdout'].strip() == 'All terms check.', checked)
   85              mutated = directory / 'parse.js'
   86              built = successful([*seed, directory / 'parse-cli.bend', '-o', mutated])
   87              case = next(c for c in cases if Path(c['file']).stem == witness)
   88              actual = run(['bun', mutated, ROOT / 'tests/subsets' / case['file']])
   89              span = case['knot']['diagnostic'].rsplit('\t', 1)[1]
   90              classified(actual, {'exit': 3 if wrong.startswith('Unsupported') else 2,
   91                                  'diagnostic': wrong + '\t' + span})
   92              require(actual['exit'] != case['knot']['exit'], actual)
   93              record['mutants'].append({'name': name, 'before': before, 'after': after,
   94                                        'typecheck': checked, 'build': built,
   95                                        'mutated_sha256': digest(target), 'witness': case['file'],
   96                                        'expected': case['knot'], 'actual': actual,
   97                                        'outcome': 'semantic-kill'})
   98          require(all(digest(ROOT / p) == h for p, h in record['inputs'].items()),
   99                  'Inputs changed during the gate')
  100          record['status'] = 'passed'
  101          print(f"PASS: {len(cases)} frozen seed outputs; {len(record['fixtures'])} parser observations; "
  102                f"{len(record['mutants'])} type-correct semantic mutants killed; "
  103                '16 filled frontend laws (6 added, 1 narrowed).')
  104      except Exception as error:
  105          record.update(status='failed', failure=str(error))
  106          raise
  107      finally:
  108          RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

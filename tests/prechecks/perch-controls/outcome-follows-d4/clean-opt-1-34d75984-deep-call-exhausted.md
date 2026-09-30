<!-- prechecks packet v1; rule=outcome-follows-d4; increment=opt-1; head=34d7598457ac; base=3a162abca884; builder=scripts/prechecks/packets@3a2ef420dff1; sources: tests/compiler-fields-wasm/check.py@34d75984 sha256=544de0f4486cc62c8ec3fe1150bf29561f0e9e3cf1570fecd07e314fe3066d74; tests/compiler-opt/SPEC.md@34d75984 sha256=d4872925164c10c339f51ace5596a2d4547be0d74bbd017071773c71e6e75ec6 -->
# Claim
Outcome claims this branch changed:

tests/compiler-opt/SPEC.md:70-71 (section: Assertions and outcomes) - verbatim text:

> The existing `deep-call` evaluator parser limit remains an explicit Exhausted
> observation; its enlarged compile/audit bounds permit Wasm and core inspection.

tests/compiler-opt/SPEC.md:74-75 (section: Assertions and outcomes) - verbatim text:

> The constrained-stack shallow control must run; deep programs may remain
> Exhausted or finish with the fixed value after optimization.

tests/compiler-opt/SPEC.md:74-76 (section: Assertions and outcomes) - verbatim text:

> The constrained-stack shallow control must run; deep programs may remain
> Exhausted or finish with the fixed value after optimization. Neither outcome is
> relabelled Invalid or Unsupported.

# Evidence
Decision rows (verbatim, docs/COMPILER-CAMPAIGN.md):

| D4 | The compile path covers the full implementation language. The checker grows alongside, never silently accepting what it cannot check. A form it cannot check is reported `Unsupported`, never `Invalid`, and never passed through unchecked. | Keeps Knot's identity as a checked compiler while it grows. |

tests/compiler-opt/SPEC.md:55-90 (section: Assertions and outcomes):

> ## Assertions and outcomes
>
> The 63 accepted corpus programs and eleven exact-tree observer programs run in
> seed-built native and Bun lanes. The 211 reference calls cover their fixed
> argument domains. Each of the three core passes also runs separately, using
> Bend entry wrappers that replace only the pipeline call with `O.apply`.
> For each lane:
>
> - Compare the seed and evaluator observations against fixed literal expectations.
> - Compare evaluation before and after optimization.
> - Invoke every recorded enum host call on unoptimized and optimized real Wasm.
> - Compare `wasm2wat`-decoded export names and function signatures.
> - Compare canonical function-body and signature observations after one and two pipeline applications. Datatypes, token spans and caches are outside this rendering.
> - Preserve the checked core function signatures and compare native/Bun bytes.
>
> The existing `deep-call` evaluator parser limit remains an explicit Exhausted
> observation; its enlarged compile/audit bounds permit Wasm and core inspection.
> The arena-overflow control may become a successful value after allocation
> elimination. Exhaustion is inconclusive about a value and is recorded separately.
> The constrained-stack shallow control must run; deep programs may remain
> Exhausted or finish with the fixed value after optimization. Neither outcome is
> relabelled Invalid or Unsupported. Harness timeout, host failure, internal
> failure, and compiler rejection are separate records.
>
> Every optimized module must target only its current function with `return_call`.
> The tail fixture must contain that instruction; the non-tail fixture must retain
> an ordinary self `call` and contain no `return_call`. Its values and
> constructor-building recursion also retain their fixed observations.
> Zero optimizer depth and zero output capacity must report their exact Exhausted
> codes. Both lanes must preserve a preexisting output on those failures and on a
> missing-source HostFailure.
> The new filled law entry must print `All terms check.` The 43 literal malformed
> and valid core controls run in both lanes, checking the independent core
> verifier's status distinctions, affine and erased use, declarations, lexical
> levels, calls, cases, descent, and exhaustion.
>

tests/compiler-opt/SPEC.md:101-114 (section: Reproduction and limits):

> ## Reproduction and limits
>
> Run `BEND_NO_TELEMETRY=1 python3 tests/compiler-opt/check.py` or the registered
> gate runner. The gate writes only its receipt and ignored `.local/compiler-opt/`
> products. It uses the pinned seed with `bun --no-env-file`, performs no dependency
> installation, and does not read `.env` files or use network services.
>
> Corpus equality is a deterministic regression claim, not a universal refinement
> proof. Pure source values remain the observational contract; bounded evaluator,
> parser, stack and arena resources remain explicit. Every current top-level
> function is exported, so the export-preserving function-DCE instance keeps every
> function. Future private functions, primitive literals, modules, and new IR
> constructors need fresh fixed domains and gates before broadening this claim.
>

Frozen expectations that name the same cause:

`tests/compiler-fields-wasm/check.py:119-279` (frozen expectation code naming `deep-call`)
```
  119  def main():
  120      BUILD.mkdir(parents=True, exist_ok=True)
  121      GENERATED.mkdir(exist_ok=True)
  122      RECEIPT.parent.mkdir(exist_ok=True)
  123      require(os.environ.get('BEND_NO_TELEMETRY') == '1', 'export BEND_NO_TELEMETRY=1')
  124      manifest = json.loads((HERE / 'cases.json').read_text())
  125      baseline = json.loads((HERE / 'enum-baseline.json').read_text())
  126      expectations = json.loads((HERE / 'expectations.json').read_text())
  127      cases = {c['name']: c for c in manifest['cases']}
  128      record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
  129                'status': 'incomplete', 'profile': 'knot-fields-wasm-1',
  130                'seed_revision': manifest['seed_revision']}
  131      try:
  132          paths = [*sorted((ROOT / 'src').glob('*.bend')), ROOT / 'src/SPEC.md',
  133                   ROOT / 'src/CONTRACT.json', HOST, *sorted(HERE.glob('*.bend')),
  134                   *sorted(HERE.glob('*.json')), *sorted(HERE.glob('*.mjs')), Path(__file__),
  135                   *sorted((HERE / 'fixtures').glob('*.bend')), *[ROOT / f for f in baseline]]
  136          record['inputs'] = {str(p.relative_to(ROOT)): digest(p) for p in paths}
  137          record['seed'] = {f: digest(ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2' / f)
  138                            for f in ('main.ts', 'bend.ts', 'comp.ts', 'base.bend')}
  139          record['tools'] = {t: successful([t, '--version'])['stdout'].strip()
  140                             for t in ('bun', 'node', 'python3', 'wasm2wat')}
  141          require(record['tools']['node'] == 'v22.22.3', record['tools'])
  142          require(len(baseline) == 25, 'frozen enum corpus')
  143          frozen = [(c['name'], call, digest(HERE / c['file'])) for c in cases.values() for call in c['calls']]
  144          require(frozen == [(o['case'], o['call'], o['source_sha256']) for o in expectations['observations']], 'expectations or fixtures drifted')
  145          record['proof'] = successful([SEED, HERE / 'PROOF.bend'])
  146          require(record['proof']['stdout'].strip() == 'All terms check.', record['proof'])
  147          record['new_laws'] = 5
  148          record['builds'], lanes = [], {}
  149          for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
  150              lanes[lane] = {}
  151              for phase, entry in [('compile', HERE / 'compile.bend'), ('eval', ROOT / 'src/eval-cli.bend')]:
  152                  output = BUILD / (phase + suffix)
  153                  result = successful([SEED, entry, '-o', output])
  154                  record['builds'].append({'lane': lane, 'phase': phase, 'result': result, 'sha256': digest(output)})
  155                  lanes[lane][phase] = [*runtime, output]
  156          record['enum_preservation'] = []
  157          for source, expected in baseline.items():
  158              for lane, commands in lanes.items():
  159                  output = BUILD / f'enum-{Path(source).stem}-{lane}.wasm'
  160                  result = compiled(commands['compile'], ROOT / source, output)
  161                  require(digest(output) == expected, ('enum bytes changed', source, lane))
  162                  require(sections(output.read_bytes()) == [1, 3, 7, 10], 'enum section contract')
  163                  record['enum_preservation'].append({'source': source, 'lane': lane, 'compile': result, 'sha256': digest(output)})
  164          record['fixtures'], modules = [], {}
  165          for case in cases.values():
  166              name, path = case['name'], HERE / case['file']
  167              item = {'name': name, 'reference': [], 'lanes': {}}
  168              for i, call in enumerate(case['calls']):
  169                  wrapper = BUILD / f'{name}-reference-{i}.bend'
  170                  imported = os.path.relpath(path, wrapper.parent)
  171                  wrapper.write_text(f'import {imported} as F\n\ndef main() -> F.{case["type"]}:\n  {call["seed"]}\n')
  172                  result = successful([SEED, wrapper])
  173                  expected = imported.removesuffix('.bend') + '.' + case['constructors'][call['tag']] + '{}'
  174                  require(result['stdout'].strip() == expected, (expected, result))
  175                  item['reference'].append({'call': call, 'result': result})
  176              modules[name] = {}
  177              for lane, commands in lanes.items():
  178                  output = BUILD / f'{name}-{lane}.wasm'
  179                  built = compiled(commands['compile'], path, output, case.get('compile_budgets', []))
  180                  modules[name][lane] = output
  181                  observations = []
  182                  for call in case['calls']:
  183                      evaluated = run([*commands['eval'], path, call['export'], 1048576, *call['arguments']])
  184                      if 'eval_exhausted' in case:
  185                          diagnostic(evaluated, 4, case['eval_exhausted'])
  186                      else:
  187                          expected = f'Evaluated\t{case["type_id"]}\t{call["tag"]}\t{case["constructors"][call["tag"]]}{{}}'
  188                          require(evaluated['exit'] == 0 and evaluated['stdout'].strip() == expected, (expected, evaluated))
  189                      wasm = run(['node', HOST, PROFILE, output, call['export'], *call['arguments']])
  190                      if name == 'arena-overflow':
  191                          diagnostic(wasm, 4, manifest['arena']['diagnostic'])
  192                      else:
  193                          require(wasm['exit'] == 0 and json.loads(wasm['stdout'])['result'] == call['tag'], (call, wasm))
  194                      observations.append({'call': call, 'evaluator': evaluated, 'wasm': wasm})
  195                  item['lanes'][lane] = {'compile': built, 'sha256': digest(output), 'observations': observations}
  196                  if lane == 'native':
  197                      heap = na
[truncated after 6,144 bytes; 6,887 bytes omitted]

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

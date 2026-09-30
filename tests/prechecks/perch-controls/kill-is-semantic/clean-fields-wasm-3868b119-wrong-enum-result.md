<!-- prechecks packet v1; rule=kill-is-semantic; increment=fields-wasm; head=3868b119f8ba; base=185b7d5ffad5; builder=scripts/prechecks/packets@3a2ef420dff1; sources: tests/compiler-fields-wasm/check.py@3868b119 sha256=544de0f4486cc62c8ec3fe1150bf29561f0e9e3cf1570fecd07e314fe3066d74 -->
# Claim
Statements about what counts as a kill:

- tests/compiler-fields-wasm/README.md: | Type-correct mutant | Frozen witness | Expected / mutant result | | --- | --- | --- | | Swapped store offsets | `pair.direct(0,1)` | 0 / 1 | | Stored erased slot | `erased.observe(0,1)` | 1 / 0 | | Wrong cell tag | `erased.ghost()` | 1 / 0 | | No pointer bump | `aliasing.observe(0,1)` | 0 / 1 | All four mutant compilers typecheck, emit decoder-valid modules, and yield the wrong enum result in both compiler lanes: 8 semantic kills.
- tests/compiler-fields-wasm/README.md: Parse/type errors, timeouts, host failures and invalid Wasm cannot satisfy these kill assertions.
- tests/compiler-fields-wasm/README.md: All four mutant compilers typecheck, emit decoder-valid modules, and yield the wrong enum result in both compiler lanes: 8 semantic kills.
- tests/compiler-fields-wasm/README.md: Parse/type errors, timeouts, host failures and invalid Wasm cannot satisfy these kill assertions. ## Proof and style boundary

# Evidence
`tests/compiler-fields-wasm/check.py:119-279` function `main`:
```python
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
  197                      heap = name not in ('deep-call', 'deep-stack')
  198                      require(sections(output.read_bytes()) == ([1, 3, 5, 6, 7, 10] if heap else [1, 3, 7, 10]), 'section profile')
  199                      wat = successful(['wasm2wat', output])['stdout']
  200                      item['instructions'] = instructions(wat, heap)
  201                      item['sections'] = sections(output.read_bytes())
  202                      shutil.copy2(output, GENERATED / (name + '.wasm'))
  203                      (GENERATED / (name + '.wat')).write_text(wat)
  204                  else:
  205                      require(output.read_bytes() == modules[name]['native'].read_bytes(), (name, 'native/Bun byte mismatch'))
  206              record['fixtures'].append(item)
  207          record['boundaries'] = []
  208          for lane in lanes:
  209              # A shallow positive control separates Node startup from invocation exhaustion.
  210              for name, status in [('pair', 0), ('deep-stack', 4)]:
  211                  result = run(['node', *manifest['stack']['node_flags'], HOST, PROFILE, modules[name][lane], 'main'])
  212                  if status == 4:
  213                      diagnostic(result, 4, manifest['stack']['diagnostic'])
  214                  else:
  215                      require(result['exit'] == 0 and json.loads(result['stdout'])['result'] == 1, result)
  216                  record['boundaries'].append({'name': 'stack-' + name, 'lane': lane, 'result': result})
  217              for name, export, count, tag, args in [('arena-overflow', 'f0', 8192, 1, []),
  218                      ('erased', 'ghost', 16384, 1, []), ('erased', 'empty', 16384, 0, []),
  219                      ('pair', 'direct', 5461, 0, [0, 1])]:
  220                  result = successful(['node', HERE / 'arena.mjs', modules[name][lane], export, count, tag, *args])
  221                  require(json.loads(result['stdout']) == {'successful': count, 'overflow': count + 1, 'repeatedOverflow': True}, result)
  222                  record['boundaries'].append({'name': 'arena-' + export, 'lane': lane, 'result': result})
  223              pair = modules['pair'][lane]
  224              bad = BUILD / 'invalid.wasm'; bad.write_bytes(b'not wasm')
  225              for label, args in [('missing-file', [PROFILE, BUILD / 'absent.wasm', 'main']),
  226                      ('invalid-module', [PROFILE, bad, 'main']),
  227                      ('unknown-profile', ['--profile=missing', pair, 'main']),
  228                      ('missing-export', [PROFILE, pair, 'absent']),
  229                      ('wrong-arity', [PROFILE, pair, 'direct', 0]),
  230                      ('argument-range', [PROFILE, pair, 'direct', 256, 0]),
  231                      ('unreachable-outside-fields-profile', [modules['arena-overflow'][lane], 'main'])]:
  232                  result = run(['node', HOST, *args]); diagnostic(result, 5, 'HostFailure\twasm\t')
  233                  record['boundaries'].append({'name': label, 'lane': lane, 'result': result})
  234              for label, budgets in [('emitter-depth', [65536, 512, 512, 0, 65536]),
  235                                     ('output-capacity', [65536, 512, 512, 4096, 32])]:
  236                  output = BUILD / f'{label}-{lane}.wasm'; output.write_bytes(b'stale')
  237                  result = run([*lanes[lane]['compile'], HERE / cases['pair']['file'], output, *budgets])
  238                  diagnostic(result, 4, 'Exhausted\temit\t')
  239                  require(output.read_bytes() == b'stale', 'exhaustion changed output')
  240                  record['boundaries'].append({'name': label, 'lane': lane, 'result': result, 'artifact_preserved': True})
  241          record['mutants'] = []
  242          for name, old, new, witness, export, args, expected in MUTANTS:
  243              directory = BUILD / name; directory.mkdir(exist_ok=True)
  244              for source in (ROOT / 'src').glob('*.bend'):
  245                  shutil.copy2(source, directory / source.name)
  246              target = directory / 'wasm.bend'; source = target.read_text()
  247              require(source.count(old) == 1, (name, 'unique mutation'))
  248              target.write_text(source.replace(old, new))
  249              entry = directory / 'entry.bend'
  250              entry.write_text((HERE / 'compile.bend').read_text().replace('../../src/', './'))
  251              checked = successful([SEED, entry, '--check-only'])
  252              require(checked['stdout'].strip() == 'All terms check.', checked)
  253              item = {'name': name, 'old': old, 'new': new, 'source_sha256': digest(target),
  254                      'typecheck': checked, 'witness': witness, 'export': export,
  255                      'arguments': args, 'expected_tag': expected, 'lanes': {}}
  256              require(any(c['export'] == export and c['arguments'] == args and c['tag'] == expected
  257                          for c in cases[witness]['calls']), 'mutant expectation must be frozen')
  258              for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
  259                  executable = directory / ('mutant' + suffix)
  260                  built = successful([SEED, entry, '-o', executable])
  261                  output = directory / f'{lane}.wasm'
  262                  emission = compiled([*runtime, executable], HERE / cases[witness]['file'], output)
  263                  successful(['wasm2wat', output])
  264                  actual = successful(['node', HOST, PROFILE, output, export, *args])
  265                  require(json.loads(actual['stdout'])['result'] != expected, (name, 'mutant survived'))
  266                  item['lanes'][lane] = {'build': built, 'emission': emission, 'actual': actual, 'outcome': 'semantic-kill'}
  267              record['mutants'].append(item)
  268          record['generated'] = {str(p.relative_to(ROOT)): digest(p) for p in sorted(GENERATED.iterdir())}
  269          require(all(digest(ROOT / p) == h for p, h in record['inputs'].items()), 'inputs changed during gate')
  270          rec
[truncated after 12,288 bytes; 721 bytes omitted]

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

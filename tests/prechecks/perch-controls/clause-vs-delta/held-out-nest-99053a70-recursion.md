<!-- prechecks packet v1; rule=clause-vs-delta; increment=nest; head=99053a70a68b; base=cc9f2fd23d59; builder=scripts/prechecks/packets@40e325337e4a; sources: src/CONTRACT.json@99053a70 sha256=f062c80622e6eb52b8dca79d62da35b9f936587359783d54a778ef066c6d5f7a; src/matrix-LAWS.bend@99053a70 sha256=905f77100e8337b040f01de1bab6f78d6720c18db3e4b3f58387467b1d6b71cd; tests/compiler-nest/check.py@99053a70 sha256=f19b820dbdec6755c362d35d677adb3da7b30d27c4bea515cec3c47784ad42f2 -->
# Claim
Invariance clause (src/CONTRACT.json):

> The compiler opens the requested output only after complete checking and bounded emission; semantic failure and exhaustion leave existing output untouched. File-write failures are HostFailure and may leave an incomplete file, never a Built result. Callers must use the exit status, not file presence, as evidence of a fresh artifact.

# Evidence
Evidence: the governed diff hunks (base to head).
```
`src/matrix-LAWS.bend:77-86` (added)
   77  law lowering_work_exhaustion:
   78    for +token: S.Token
   79    for columns: List<&2,S.Node>
   80    for rows: List<&2,S.Node>
   81    for types: List<&2,C.Datatype>
   82    for scope: E.Scope
   83    {M.step(token,columns,rows,0,types,scope) == Fail{S.Exhausted{"check",S.at(token)}} : Result<S.Error,S.Node>}
   84  
   85  # A literal inhabited two-constructor catalog supports complete lowering laws.
   86  # These normalizations include checking, quantities and the emitted core tree.

`tests/compiler-nest/check.py:71-75` (added)
   71  def compiled(command, source, output):
   72      output.unlink(missing_ok=True)
   73      result = successful([*command, source, output])
   74      require(output.exists() and result['stdout'].strip() == f'Built\t{output.stat().st_size}', result)
   75      return result

`tests/compiler-nest/check.py:106-152` (added)
  106  def fixtures(record, manifest, lanes):
  107      for case in manifest['fixtures']:
  108          require(digest(ROOT / case['file']) == case['sha256'], ('fixture hash', case['name']))
  109          fields = 'fields' in case['requires']
  110          item = {'name': case['name'], 'file': case['file'], 'sha256': case['sha256'],
  111                  'expected': case['knot'], 'profile': 'knot-fields-wasm-1' if fields else 'knot-enum-1', 'lanes': {}}
  112          accepted = case['knot']['outcome'] == 'Accepted'
  113          pending = case['name'] in UNMET
  114          expected = {'exit': 3, 'diagnostic': 'Unsupported\tcheck\trecursive-call\t'} if pending else case['knot']
  115          module_hashes = []
  116          for lane, commands in lanes.items():
  117              source = ROOT / case['file']
  118              check = run([*commands['check'], source])
  119              item['lanes'][lane] = {'check': check}
  120              output = BUILD / f"{case['name']}-{lane}.wasm"
  121              if accepted:
  122                  checked(check)
  123                  compile_result = compiled(commands['fields' if fields else 'enum'], source, output)
  124                  module_hashes.append(digest(output))
  125                  decoder = successful(['wasm2wat', output])
  126                  item['lanes'][lane].update(compile=compile_result, module_sha256=digest(output),
  127                                             wat_sha256=hashlib.sha256(decoder['stdout'].encode()).hexdigest(), calls=[])
  128                  if not fields:
  129                      item['lanes'][lane]['instructions'] = _enum_contract.mvp_instructions(decoder['stdout'])
  130                  for call in calls(case):
  131                      evaluation = run([*commands['eval'], source, call['export'], 65536, *call['ordinals']])
  132                      evaluated(evaluation, call)
  133                      execution = executed(output, call, fields)
  134                      item['lanes'][lane]['calls'].append({'export': call['export'], 'ordinals': call['ordinals'],
  135                          'type_id': call['type_id'], 'tag': call['tag'], 'eval': evaluation, 'wasm': execution})
  136              else:
  137                  diagnostic(check, expected)
  138                  evaluation = run([*commands['eval'], source, 'main', 65536])
  139                  diagnostic(evaluation, expected)
  140                  marker = b'existing artifact: rejection must preserve this\n'
  141                  output.write_bytes(marker)
  142                  compile_result = run([*commands['fields' if fields else 'enum'], source, output])
  143                  diagnostic(compile_result, expected)
  144                  require(output.read_bytes() == marker, ('output changed', compile_result))
  145                  item['lanes'][lane].update(eval=evaluation, compile=compile_result, artifact_preserved=True)
  146          if accepted:
  147              require(len(set(module_hashes)) == 1, ('native/Bun bytes', case['name'], module_hashes))
  148          if pending:
  149              item['disposition'] = 'unmet: seed rejects; complete decreasing-call rule is not implemented'
  150              record['unmet'].append(item)
  151          else:
  152              record['fixtures'].append(item)

`tests/compiler-nest/check.py:155-198` (added)
  155  def controls(record, fixed, lanes):
  156      wrapper = ROOT / '.local/nest/tree-shallow.bend'
  157      wrapper.parent.mkdir(parents=True, exist_ok=True)
  158      wrapper.write_text('import ../../tests/compiler-nest/controls/tree-arena.bend as F\n\ndef main() -> F.Flag:\n  F.shallow()\n')
  159      for name, case in fixed['fixtures'].items():
  160          source = ROOT / case['file']
  161          require(digest(source) == case['sha256'], ('control changed', name))
  162          ref = run(case['seed']['command'])
  163          require(all(ref[k] == case['seed'][k] for k in ('exit', 'stdout', 'stderr')), (case['seed'], ref))
  164          if name == 'tree-arena':
  165              shallow = run(case['shallow_seed']['command'])
  166              require(all(shallow[k] == case['shallow_seed'][k] for k in ('exit', 'stdout', 'stderr')), shallow)
  167          for lane, commands in lanes.items():
  168              if name == 'tree-arena':
  169                  check = run([*commands['check'], source]); checked(check)
  170                  output = BUILD / f'tree-arena-{lane}.wasm'
  171                  compile_result = compiled(commands['fields'], source, output)
  172                  record['boundaries'].append({'name': name, 'lane': lane, 'phase': 'check', 'result': check})
  173                  record['boundaries'].append({'name': name, 'lane': lane, 'phase': 'compile', 'result': compile_result,
  174                                               'module_sha256': digest(output)})
  175                  for entry, expected in case['expectations'].items():
  176                      evaluation = successful([*commands['eval'], source, entry, 1048576])
  177                      require(evaluation['stdout'].strip() == expected['eval'], evaluation)
  178                      execution = run(['node', HOST, FIELDS, output, entry])
  179                      if 'wasm_exit' in expected:
  180                          diagnostic(execution, {'exit': expected['wasm_exit'], 'diagnostic': expected['wasm_diagnostic']})
  181                      else:
  182                          require(execution['exit'] == 0 and not execution['stderr']
  183                                  and json.loads(execution['stdout'])['result'] == expected['wasm'], execution)
  184                      record['boundaries'].append({'name': name, 'lane': lane, 'export': entry, 'phase': 'eval', 'result': evaluation})
  185                      record['boundaries'].append({'name': name, 'lane': lane, 'export': entry, 'phase': 'wasm', 'result': execution})
  186              else:
  187                  for phase in ('check', 'eval', 'fields'):
  188                      output = BUILD / f'{name}-{lane}-rejected.wasm'
  189                      marker = b'control artifact must survive\n'
  190                      args = [source]
  191                      if phase == 'eval':
  192                          args += ['main', 65536]
  193                      elif phase == 'fields':
  194                          output.write_bytes(marker); args += [output]
  195                      actual = run([*commands[phase], *args]); diagnostic(actual, case['expectations'])
  196                      if phase == 'fields':
  197                          require(output.read_bytes() == marker, ('control output changed', actual))
  198                      record['boundaries'].append({'name': name, 'lane': lane, 'phase': phase, 'result': actual})

`tests/compiler-nest/check.py:309-361` (added)
  309  def main():
  310      BUILD.mkdir(parents=True, exist_ok=True)
  311      RECEIPT.parent.mkdir(parents=True, exist_ok=True)
  312      manifest = json.loads((HERE / 'expectations.json').read_text())
  313      fixed = json.loads((HERE / 'control-expectations.json').read_text())
  314      paths = [*sorted((ROOT / 'src').glob('*.bend')), ROOT / 'src/SPEC.md', ROOT / 'src/CONTRACT.json',
  315               *sorted(HERE.glob('*.py')), *sorted(HERE.glob('*.json')), *sorted(HERE.glob('*.md')),
  316               *sorted((HERE / 'fixtures').glob('*.bend')), *sorted((HERE / 'controls').glob('*.bend')),
  317               ROOT / 'tests/compiler-fields-wasm/compile.bend', ROOT / 'tests/compiler-fields-wasm/enum-baseline.json', HOST]
  318      record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'incomplete',
  319                'inputs': {str(p.relative_to(ROOT)): digest(p) for p in paths},
  320                'seed': manifest['seed'], 'frozen_tools': manifest['tools'],
  321                'builds': [], 'fixtures': [], 'unmet': [], 'mutants': [], 'boundaries': [], 'enum_preservation': []}
  322      try:
  323          record['oracle'] = successful(['python3', HERE / 'regen.py'])
  324          require('no differences' in record['oracle']['stdout'], record['oracle'])
  325          record['tools'] = {tool: successful([tool, '--version'])['stdout'].strip()
  326                             for tool in ('bun', 'node', 'python3', 'wasm2wat')}
  327          require(record['tools']['node'] == 'v22.22.3' and record['tools']['bun'] == '1.3.14', record['tools'])
  328          record['proof'] = successful([*SEED, ROOT / 'src/matrix-PROOF.bend'])
  329          require(record['proof']['stdout'].strip() == 'All terms check.', record['proof'])
  330          lanes = build_lanes(record)
  331          fixtures(record, manifest, lanes)
  332          controls(record, fixed, lanes)
  333          enum_bytes(record, lanes)
  334          mutants(record, manifest, fixed)
  335          require(all(digest(ROOT / p) == h for p, h in record['inputs'].items()), 'Inputs changed during gate')
  336          record['counts'] = {
  337              'seed_fixtures': len(manifest['fixtures']),
  338              'seed_entry_calls': sum(len(c['observed']['calls']) for c in manifest['fixtures']),
  339              'matched_frozen_outcomes': len(record['fixtures']), 'unmet_frozen_outcomes': len(record['unmet']),
  340              'check_observations': 2 * len(record['fixtures']),
  341              'unmet_phase_observations': 6 * len(record['unmet']),
  342              'accepted_books': sum(c['expected']['exit'] == 0 for c in record['fixtures']),
  343              'evaluation_values': sum(len(lane.get('calls', [])) for c in record['fixtures'] for lane in c['lanes'].values()),
  344              'wasm_values': sum(len(lane.get('calls', [])) for c in record['fixtures'] for lane in c['lanes'].values()),
  345              'rejected_phase_observations': sum(3 * len(c['lanes']) for c in record['fixtures'] if c['expected']['exit'] != 0),
  346              'boundary_observations': len(record['boundaries']), 'enum_hash_checks': len(record['enum_preservation']),
  347              'mutants': len(record['mutants']), 'semantic_kills': sum(len(c['lanes']) for c in record['mutants'])}
  348          record['qualification'] = {'complete': not record['unmet'],
  349              'limits': 'The gate monitors two authorized conservative recursion outcomes; neither is counted as frozen conformance.'}
  350          record['status'] = 'passed'
  351      except Exception as error:
  352          record['failure'] = repr(error)
  353          raise
  354      finally:
  355          RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
  356      c = record['counts']
  357      print(f"Nest gate passed within stated scope: {c['seed_fixtures']} seed fixtures, {c['seed_entry_calls']} seed calls; "
  358            f"{c['matched_frozen_outcomes']}/40 frozen outcomes, {c['unmet_frozen_outcomes']} UNMET; "
  359            f"{c['evaluation_values']} evaluator values, {c['wasm_values']} Wasm values, "
  360            f"{c['boundary_observations']} boundary observations, {c['enum_hash_checks']} enum hashes, "
  361            f"{c['mutants']} mutants / {c['semantic_kills']} semantic kills")
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

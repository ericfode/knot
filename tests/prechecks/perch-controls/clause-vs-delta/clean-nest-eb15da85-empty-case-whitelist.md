<!-- prechecks packet v1; rule=clause-vs-delta; increment=nest; head=eb15da857dc7; base=3c25d9bede00; builder=scripts/prechecks/packets@3a2ef420dff1; sources: src/matrix-PROOF.bend@eb15da85 sha256=84d79973f76c766b3bfcd97dfe6f913974e9d2962c32b65781db84aa65a9ca31; tests/compiler-nest/SPEC.md@eb15da85 sha256=d85ee3b860e845faca82fe6dabcb1c6bec8dbd93270db229a170ab696b71c467; tests/compiler-nest/check.py@eb15da85 sha256=f19b820dbdec6755c362d35d677adb3da7b30d27c4bea515cec3c47784ad42f2; tests/compiler-nest/review.py@eb15da85 sha256=a017b7974c6b1a3c25906b21a85c02f11faddfc469164639caf31dbb18c58dba -->
# Claim
Invariance clause (tests/compiler-nest/SPEC.md):

> A checked empty case emits `i32.const 0`; it has no domain-valid execution. The enum whitelist is unchanged and is checked on every enum-profile nest module.

# Evidence
Evidence: the governed diff hunks (base to head).
```
`src/matrix-PROOF.bend:94-94` (added)
   94  def L.empty_reference_stays_live(name,level,q,type_id,live): {==}

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

`tests/compiler-nest/review.py:20-57` (added)
   20  def fixtures(record, manifest, lanes):
   21      for case in manifest['fixtures']:
   22          source = gate.ROOT / case['file']
   23          gate.require(gate.digest(source) == case['sha256'], ('review fixture hash', case['name']))
   24          item = {'name': case['name'], 'lanes': {}}
   25          hashes = []
   26          for lane, commands in lanes.items():
   27              observed = {'check': gate.run([*commands['check'], source])}
   28              output = BUILD / f'{case["name"]}-{lane}.wasm'
   29              if case['knot']['exit'] == 0:
   30                  gate.checked(observed['check'])
   31                  observed['compile'] = gate.compiled(commands['fields' if case['fields'] else 'enum'], source, output)
   32                  hashes.append(gate.digest(output))
   33                  wat = gate.successful(['wasm2wat', output])['stdout']
   34                  observed['module_sha256'] = gate.digest(output)
   35                  if not case['fields']:
   36                      observed['instructions'] = enum_gate.mvp_instructions(wat)
   37                  observed['calls'] = []
   38                  for call in case['calls']:
   39                      value = gate.run([*commands['eval'], source, call['export'], 65536, *call['ordinals']])
   40                      gate.evaluated(value, call)
   41                      wasm = gate.executed(output, call, case['fields'])
   42                      observed['calls'].append({'export': call['export'], 'arguments': call['ordinals'], 'eval': value, 'wasm': wasm})
   43              else:
   44                  gate.diagnostic(observed['check'], case['knot'])
   45                  observed['eval'] = gate.run([*commands['eval'], source, 'main', 65536])
   46                  gate.diagnostic(observed['eval'], case['knot'])
   47                  # Both public profiles must reject before opening an artifact.
   48                  for profile in ('enum', 'fields'):
   49                      output.write_bytes(b'preserve rejected artifact\n')
   50                      result = gate.run([*commands[profile], source, output])
   51                      gate.diagnostic(result, case['knot'])
   52                      gate.require(output.read_bytes() == b'preserve rejected artifact\n', result)
   53                      observed[profile] = result
   54              item['lanes'][lane] = observed
   55          if hashes:
   56              gate.require(len(set(hashes)) == 1, ('review native/Bun module equality', hashes))
   57          record['fixtures'].append(item)

`tests/compiler-nest/review.py:84-121` (added)
   84  def enum_control(record, lanes):
   85      source = HERE / 'fixtures/empty-type.bend'
   86      for lane, commands in lanes.items():
   87          output = BUILD / f'empty-{lane}.wasm'
   88          result = gate.compiled(commands['enum'], source, output)
   89          wat = gate.successful(['wasm2wat', output])['stdout']
   90          ops = enum_gate.mvp_instructions(wat)
   91          gate.require('unreachable' not in ops and 'i32.const' in ops, ops)
   92          record['enum_whitelist'].append({'lane': lane, 'compile': result, 'instructions': ops,
   93                                           'sha256': gate.digest(output)})
   94      directory = BUILD / 'empty-unreachable'
   95      directory.mkdir(exist_ok=True)
   96      for source_file in (gate.ROOT / 'src').glob('*.bend'):
   97          shutil.copy2(source_file, directory / source_file.name)
   98      target = directory / 'wasm.bend'
   99      text = target.read_text()
  100      old = 'Branches{Nil{},index,pointer}: code(W.bytes(cap,[65,0]),next)'
  101      gate.require(text.count(old) == 1, 'empty encoding mutation anchor')
  102      target.write_text(text.replace(old, 'Branches{Nil{},index,pointer}: code(W.bytes(cap,[0]),next)'))
  103      proof = gate.successful([*gate.SEED, directory / 'compile-cli.bend', '--check-only'])
  104      gate.require(proof['stdout'].strip() == 'All terms check.', proof)
  105      item = {'name': 'empty-unreachable', 'typecheck': proof, 'lanes': {}}
  106      for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
  107          binary = directory / ('compile' + suffix)
  108          gate.successful([*gate.SEED, directory / 'compile-cli.bend', '-o', binary])
  109          output = directory / f'{lane}.wasm'
  110          gate.compiled([*runtime, binary], source, output)
  111          wat = gate.successful(['wasm2wat', output])['stdout']
  112          # The mutant is a valid executable module; only the declared whitelist kills it.
  113          gate.executed(output, {'export': 'main', 'ordinals': [], 'tag': 1}, False)
  114          try:
  115              enum_gate.mvp_instructions(wat)
  116          except AssertionError as error:
  117              gate.require('unreachable' in str(error), error)
  118              item['lanes'][lane] = {'outcome': 'semantic-kill', 'assertion': str(error)}
  119          else:
  120              raise AssertionError('empty-unreachable survived')
  121      record['mutants'].append(item)
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

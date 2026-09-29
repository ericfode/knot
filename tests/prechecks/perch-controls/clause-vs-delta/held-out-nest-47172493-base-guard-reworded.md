<!-- prechecks packet v1; rule=clause-vs-delta; increment=nest; head=47172493a756; base=cc9f2fd23d59; builder=scripts/prechecks/packets@3a2ef420dff1; sources: src/CONTRACT.json@47172493 sha256=19cee68f98b13c2f7bfcc0eae0c2d23134956ece18e5a326fcb2ae5018b297d7 -->
# Claim
Invariance clause at base (src/CONTRACT.json), reworded or removed by this branch:

> unsigned size > 65536 - bump; only unreachable in the profile

# Evidence
Evidence: the document change that rewords or removes the clause (unified diff, base to head).
```diff
@@ -173,3 +176,3 @@
       "initial_bump": 0,
-      "guard": "unsigned size > 65536 - bump; only unreachable in the profile",
+      "guard": "unsigned size > 65536 - bump; the only unreachable in the profile",
       "allocation": "Arguments saved before allocation; stores after bounded pointer advance",
```

Evidence: the changed code regions that share the most words with the clause.
```
`src/matrix.bend:39-43` (added)
   39  def binder(+token: S.Token, +types: List<&2,C.Datatype>) -> Result<S.Error,Unit>:
   40    S.choose(Result<S.Error,Unit>,G.constructor_before(types,token),u =>
   41      C.invalid(Unit,"constructor-pattern-binder",token),u => Done{Unit{}})
   42  
   43  # Validate source patterns, including unreachable rows, before selecting bodies.

`tests/compiler-nest/check.py:20-20` (added)
   20  FIELDS = '--profile=knot-fields-wasm-1'

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

`tests/compiler-nest/check.py:296-306` (added)
  296  def enum_bytes(record, lanes):
  297      baseline = json.loads((ROOT / 'tests/compiler-fields-wasm/enum-baseline.json').read_text())
  298      require(len(baseline) == 25, 'frozen enum module count')
  299      for source, expected in baseline.items():
  300          for lane, commands in lanes.items():
  301              for profile in ('enum', 'fields'):
  302                  output = BUILD / f'enum-{Path(source).stem}-{lane}-{profile}.wasm'
  303                  build = compiled(commands[profile], ROOT / source, output)
  304                  require(digest(output) == expected, (source, lane, profile, expected, digest(output)))
  305                  record['enum_preservation'].append({'file': source, 'lane': lane, 'profile': profile,
  306                                                     'sha256': digest(output), 'build': build})

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

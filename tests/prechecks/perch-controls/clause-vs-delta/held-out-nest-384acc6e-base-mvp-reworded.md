<!-- prechecks packet v1; rule=clause-vs-delta; increment=nest; head=384acc6e83c5; base=cc9f2fd23d59; builder=scripts/prechecks/packets@3a2ef420dff1; sources: src/SPEC.md@384acc6e sha256=a11dba1814b3c8e7464576926218853acbe7b4f83159aeddfab086429bb487d8 -->
# Claim
Invariance clause at base (src/SPEC.md), reworded or removed by this branch:

> Emit an actual Wasm binary with version 1 header and only MVP numeric/control instructions.

# Evidence
Evidence: the changed code regions that share the most words with the clause.
```
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

`tests/compiler-nest/regen.py:151-156` (added)
  151  def environment():
  152      bun = run(['bun', '--version'])
  153      seed = {'entry': SEED, 'version': '2.0.29',
  154              'revision': '574b6d39a235b539eb19a5c532993a0abb3d11ad',
  155              'sha256': {s: sha256(ROOT / SEED_DIR / s) for s in SEED_SOURCES}}
  156      return seed, {'bun': bun['stdout'].strip()}

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

`tests/compiler-nest/round3_seed.py:25-44` (added)
   25  REJECTED = {
   26      'dotted-binder': {
   27          **{name: invalid('parse', 'pattern-binder') for name in (
   28              'dot-multi-column', 'dot-variable-row', 'dot-nested-field', 'dot-flat-field',
   29              'dot-promotion', 'dot-anonymous', 'dot-constructor-name')},
   30          **{name: invalid('parse', 'binding-name') for name in ('dot-let', 'dot-let-reusable', 'dot-let-typed')},
   31          **{name: invalid('lex', 'name') for name in (
   32              'name-trailing-dot', 'name-double-dot', 'name-digit-segment',
   33              'name-type-double-dot', 'name-field-double-dot')},
   34      },
   35      'empty-binding': {name: invalid('check', 'missing-arm') for name in (
   36          'empty-after-multi', 'empty-after-control', 'empty-after-flat', 'empty-erased-control',
   37          'empty-field-after', 'empty-field-after-flat', 'empty-field-after-nested', 'empty-field-erased',
   38          'empty-param-after-field', 'empty-param-after-nested', 'empty-alias-erased')},
   39      'line-broken-header': {
   40          'line-missing-colon': invalid('parse', 'expected-:'),
   41          'line-scrutinee-missing-colon': invalid('parse', 'expected-:'),
   42          'line-trailing-comma': invalid('parse', 'expected-term'),
   43      },
   44  }
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

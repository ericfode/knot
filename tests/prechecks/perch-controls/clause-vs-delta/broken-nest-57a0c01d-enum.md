<!-- prechecks packet v1; rule=clause-vs-delta; increment=nest; head=57a0c01df87f; base=d14418b7cb04; builder=scripts/prechecks/packets@47dbd98ca1c7; sources: src/CONTRACT.json@57a0c01d sha256=a8003b0a3b6f673dda1a3b022641475944193df2b31a846dc05a2f570d674ed0; src/catalog-LAWS.bend@57a0c01d sha256=b29691c14ea3927fa3390c715f9616c89c75b43973ae550192ae351915d98bf3; src/matrix-LAWS.bend@57a0c01d sha256=872942aaf3936e939f50caea516c4305824a737aac7c7791d38e1b6f87bf8d76; src/matrix-PROOF.bend@57a0c01d sha256=3a6d3c19fce3e6f2fb562bbf964198e8411d4d2b4cfc4e41d2233200991ccdc9; tests/compiler-nest/check.py@57a0c01d sha256=b0fc9e5f895a2ae18a7ce7234ce6def1df23fe0af25c3f852780dd49cef3b5d7; tests/compiler-nest/regen.py@57a0c01d sha256=c561615d5652d50f632abd6c05044733a0866148c96337033557c19bdfac2249 -->
# Claim
Invariance clause (src/CONTRACT.json):

> unsigned size > 65536 - bump; the only reachable unreachable for domain-valid fields-profile calls

# Evidence
Evidence: the governed diff hunks (base to head).
```
diff --git a/src/catalog-LAWS.bend b/src/catalog-LAWS.bend
index dcc3879f..682ee5c6 100644
--- a/src/catalog-LAWS.bend
+++ b/src/catalog-LAWS.bend
@@ -32,2 +32,8 @@ law field_capability_is_not_acceptance:
   for rest: List<&2,C.Constructor>
   {K.enum_constructors(Con{C.Constructor{token,Con{head,tail}},rest}) == Fail{S.Unsupported{"check","constructor-fields",S.at(token)}} : Result<S.Error,Unit>}
+
+# An empty datatype is a valid catalog entry; no source value inhabits it.
+law empty_datatype:
+  for +name: S.Token
+  for +data: Bool
+  {G.datatype(Nil{},name,data) == Done{C.Datatype{name,data,Nil{}}} : Result<S.Error,C.Datatype>}

`src/matrix-LAWS.bend:6-9` (added)
    6  import ./check.bend as K
    7  
    8  # Independent observation: row identities only, with no generated fields,
    9  # aliases, scopes or bodies. Specialization must be a stable selection.

`src/matrix-LAWS.bend:130-137` (added)
  130  law default_completes_missing_branch:
  131    for +name: S.Token
  132    for fields: List<&2,C.Parameter>
  133    for +ctors: List<&2,C.Constructor>
  134    for +explicit: List<&2,S.Token>
  135    for absent: {M.named(explicit,name) == False{} : Bool}
  136    {M.defaults(Con{C.Constructor{name,fields},ctors},explicit) == Con{name,M.defaults(ctors,explicit)} : List<&2,S.Token>}
  137  

`src/matrix-PROOF.bend:64-64` (added)
   64  def L.irrefutable_specialization(arm,name,rest,body,rows,ctor,fields,level): {==}

`tests/compiler-nest/check.py:19-19` (added)
   19  FIELDS = '--profile=knot-fields-wasm-1'

`tests/compiler-nest/check.py:102-146` (added)
  102  def fixtures(record, manifest, lanes):
  103      for case in manifest['fixtures']:
  104          require(digest(ROOT / case['file']) == case['sha256'], ('fixture hash', case['name']))
  105          fields = 'fields' in case['requires']
  106          item = {'name': case['name'], 'file': case['file'], 'sha256': case['sha256'],
  107                  'expected': case['knot'], 'profile': 'knot-fields-wasm-1' if fields else 'knot-enum-1', 'lanes': {}}
  108          accepted = case['knot']['outcome'] == 'Accepted'
  109          pending = case['name'] in UNMET
  110          expected = {'exit': 3, 'diagnostic': 'Unsupported\tcheck\trecursive-call\t'} if pending else case['knot']
  111          module_hashes = []
  112          for lane, commands in lanes.items():
  113              source = ROOT / case['file']
  114              check = run([*commands['check'], source])
  115              item['lanes'][lane] = {'check': check}
  116              output = BUILD / f"{case['name']}-{lane}.wasm"
  117              if accepted:
  118                  checked(check)
  119                  compile_result = compiled(commands['fields' if fields else 'enum'], source, output)
  120                  module_hashes.append(digest(output))
  121                  decoder = successful(['wasm2wat', output])
  122                  item['lanes'][lane].update(compile=compile_result, module_sha256=digest(output),
  123                                             wat_sha256=hashlib.sha256(decoder['stdout'].encode()).hexdigest(), calls=[])
  124                  for call in calls(case):
  125                      evaluation = run([*commands['eval'], source, call['export'], 65536, *call['ordinals']])
  126                      evaluated(evaluation, call)
  127                      execution = executed(output, call, fields)
  128                      item['lanes'][lane]['calls'].append({'export': call['export'], 'ordinals': call['ordinals'],
  129                          'type_id': call['type_id'], 'tag': call['tag'], 'eval': evaluation, 'wasm': execution})
  130              else:
  131                  diagnostic(check, expected)
  132                  evaluation = run([*commands['eval'], source, 'main', 65536])
  133                  diagnostic(evaluation, expected)
  134                  marker = b'existing artifact: rejection must preserve this\n'
  135                  output.write_bytes(marker)
  136                  compile_result = run([*commands['fields' if fields else 'enum'], source, output])
  137                  diagnostic(compile_result, expected)
  138                  require(output.read_bytes() == marker, ('output changed', compile_result))
  139                  item['lanes'][lane].update(eval=evaluation, compile=compile_result, artifact_preserved=True)
  140          if accepted:
  141              require(len(set(module_hashes)) == 1, ('native/Bun bytes', case['name'], module_hashes))
  142          if pending:
  143              item['disposition'] = 'unmet: seed rejects; complete decreasing-call rule is not implemented'
  144              record['unmet'].append(item)
  145          else:
  146              record['fixtures'].append(item)

`tests/compiler-nest/check.py:290-300` (added)
  290  def enum_bytes(record, lanes):
  291      baseline = json.loads((ROOT / 'tests/compiler-fields-wasm/enum-baseline.json').read_text())
  292      require(len(baseline) == 25, 'frozen enum module count')
  293      for source, expected in baseline.items():
  294          for lane, commands in lanes.items():
  295              for profile in ('enum', 'fields'):
  296                  output = BUILD / f'enum-{Path(source).stem}-{lane}-{profile}.wasm'
  297                  build = compiled(commands[profile], ROOT / source, output)
  298                  require(digest(output) == expected, (source, lane, profile, expected, digest(output)))
  299                  record['enum_preservation'].append({'file': source, 'lane': lane, 'profile': profile,
  300                                                     'sha256': digest(output), 'build': build})

`tests/compiler-nest/check.py:303-355` (added)
  303  def main():
  304      BUILD.mkdir(parents=True, exist_ok=True)
  305      RECEIPT.parent.mkdir(parents=True, exist_ok=True)
  306      manifest = json.loads((HERE / 'expectations.json').read_text())
  307      fixed = json.loads((HERE / 'control-expectations.json').read_text())
  308      paths = [*sorted((ROOT / 'src').glob('*.bend')), ROOT / 'src/SPEC.md', ROOT / 'src/CONTRACT.json',
  309               *sorted(HERE.glob('*.py')), *sorted(HERE.glob('*.json')), *sorted(HERE.glob('*.md')),
  310               *sorted((HERE / 'fixtures').glob('*.bend')), *sorted((HERE / 'controls').glob('*.bend')),
  311               ROOT / 'tests/compiler-fields-wasm/compile.bend', ROOT / 'tests/compiler-fields-wasm/enum-baseline.json', HOST]
  312      record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'incomplete',
  313                'inputs': {str(p.relative_to(ROOT)): digest(p) for p in paths},
  314                'seed': manifest['seed'], 'frozen_tools': manifest['tools'],
  315                'builds': [], 'fixtures': [], 'unmet': [], 'mutants': [], 'boundaries': [], 'enum_preservation': []}
  316      try:
  317          record['oracle'] = successful(['python3', HERE / 'regen.py'])
  318          require('no differences' in record['oracle']['stdout'], record['oracle'])
  319          record['tools'] = {tool: successful([tool, '--version'])['stdout'].strip()
  320                             for tool in ('bun', 'node', 'python3', 'wasm2wat')}
  321          require(record['tools']['node'] == 'v22.22.3' and record['tools']['bun'] == '1.3.14', record['tools'])
  322          record['proof'] = successful([*SEED, ROOT / 'src/matrix-PROOF.bend'])
  323          require(record['proof']['stdout'].strip() == 'All terms check.', record['proof'])
  324          lanes = build_lanes(record)
  325          fixtures(record, manifest, lanes)
  326          controls(record, fixed, lanes)
  327          enum_bytes(record, lanes)
  328          mutants(record, manifest, fixed)
  329          require(all(digest(ROOT / p) == h for p, h in record['inputs'].items()), 'Inputs changed during gate')
  330          record['counts'] = {
  331              'seed_fixtures': len(manifest['fixtures']),
  332              'seed_entry_calls': sum(len(c['observed']['calls']) for c in manifest['fixtures']),
  333              'matched_frozen_outcomes': len(record['fixtures']), 'unmet_frozen_outcomes': len(record['unmet']),
  334              'check_observations': 2 * len(record['fixtures']),
  335              'unmet_phase_observations': 6 * len(record['unmet']),
  336              'accepted_books': sum(c['expected']['exit'] == 0 for c in record['fixtures']),
  337              'evaluation_values': sum(len(lane.get('calls', [])) for c in record['fixtures'] for lane in c['lanes'].values()),
  338              'wasm_values': sum(len(lane.get('calls', [])) for c in record['fixtures'] for lane in c['lanes'].values()),
  339              'rejected_phase_observations': sum(3 * len(c['lanes']) for c in record['fixtures'] if c['expected']['exit'] != 0),
  340              'boundary_observations': len(record['boundaries']), 'enum_hash_checks': len(record['enum_preservation']),
  341              'mutants': len(record['mutants']), 'semantic_kills': sum(len(c['lanes']) for c in record['mutants'])}
  342          record['qualification'] = {'complete': not record['unmet'],
  343              'limits': 'The gate monitors two authorized conservative recursion outcomes; neither is counted as frozen conformance.'}
  344          record['status'] = 'passed'
  345      except Exception as error:
  346          record['failure'] = repr(error)
  347          raise
  348      finally:
  349          RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
  350      c = record['counts']
  351      print(f"Nest gate passed within stated scope: {c['seed_fixtures']} seed fixtures, {c['seed_entry_calls']} seed calls; "
  352            f"{c['matched_frozen_outcomes']}/40 frozen outcomes, {c['unmet_frozen_outcomes']} UNMET; "
  353            f"{c['evaluation_values']} evaluator values, {c['wasm_values']} Wasm values, "
  354            f"{c['boundary_observations']} boundary observations, {c['enum_hash_checks']} enum hashes, "
  355            f"{c['mutants']} mutants / {c['semantic_kills']} semantic kills")

`tests/compiler-nest/regen.py:116-148` (added)
  116  def observe(fixture):
  117      """Run the seed on the fixture itself, then on every entry over its whole domain."""
  118      path = ROOT / fixture['file']
  119      source = path.read_text()
  120      enums, entries, type_ids = boundary(source)
  121      argv = ['bun', SEED, fixture['file']]
  122      main = {'command': argv, **run(argv)}
  123      result = entries.get('main', {}).get('result')
  124      if main['exit'] == 0 and result is not None:
  125          name = decode(main['stdout'], '', enums[result])
  126          main.update({'result_type': result, 'type_id': type_ids[result], 'result': name,
  127                       'tag': enums[result].index(name) if name else None})
  128      calls = []
  129      if main['exit'] == 0:
  130          for export, sig in entries.items():
  131              if export == 'main':
  132                  continue
  133              for arguments in itertools.product(*(enums[t] for t in sig['parameters'])):
  134                  wpath, wsource, call, prefix = wrapper(fixture, export, list(arguments), sig['result'])
  135                  (ROOT / wpath).parent.mkdir(parents=True, exist_ok=True)
  136                  (ROOT / wpath).write_text(wsource)
  137                  argv = ['bun', SEED, wpath]
  138                  obs = run(argv)
  139                  name = decode(obs['stdout'], prefix, enums[sig['result']]) if obs['exit'] == 0 else None
  140                  calls.append({
  141                      'export': export, 'arguments': list(arguments),
  142                      'ordinals': [enums[t].index(a) for t, a in zip(sig['parameters'], arguments)],
  143                      'result_type': sig['result'], 'type_id': type_ids[sig['result']],
  144                      'result': name, 'tag': enums[sig['result']].index(name) if name else None,
  145                      'seed_call': call, 'wrapper': wpath, 'wrapper_source': wsource,
  146                      'command': argv, **obs})
  147      return ({'sha256': sha256(path), 'observed': {'main': main, 'calls': calls}},
  148              enums, entries, source)
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

<!-- prechecks packet v1; rule=kill-is-semantic; increment=descent-2; head=75e1ac69852c; base=57a0c01df87f; builder=scripts/prechecks/packets@3a2ef420dff1; sources: tests/compiler-descent/check.py@75e1ac69 sha256=92e280b55f2d73c6cf0bc56ed44a9cba12111f382f7aa68790950528f400aa2b -->
# Claim
Statements about what counts as a kill:

- docs/compiler-campaign/DESCENT-2.md: | Gate | Passed coverage | | --- | --- | | `frontend` | 14 parser fixtures / 28 observations; 24 boundaries; 4 mutants; 12 classification fixtures / 24 lane observations / 72 downstream observations; 7 classification mutants; 4 boundary and 6 classification laws | | `checker` | 49 fixtures / 98 observations; 10 depth probes; 16 catalog-bound observations; 7 mutants | | `structural` | 16 fixtures / 64 catalog/compiler observations; 4 boundary pairs; 7 mutants | | `fields` | 40 fixtures / 240 phase observations; 36 budgets; 6 host probes; 12 level/inspection observations; 9 mutants | | `wasm` | 25 programs / 90 reference calls in 2 lanes; 62 rejection pairs; 44 boundaries; 7 mutants | | `wasm-trust` | 3 entries; 0 proof holes | | `fields-trust` | 4 entries; 0 proof holes | | `structural-trust` | 2 entries; 0 proof holes | | `owned-store` | 3,532 cases in 2 lanes; 15 literal witnesses; 6 mutants | | `flat-store` | 13,621 observations, 3,534 instances, 2 installed boundary states and 7 lifecycle checks per lane; 2 lanes; 9 mutants | | `recursion` | 19 fixtures / 114 phase observations; 4 fuel probes; 3 mutants | | `fields-wasm` | 8 fixtures / 32 seed calls; 64 evaluator and 64 Node observations; 50 enum byte checks; 30 boundaries; 4 mutants / 8 lane kills; 5 new checked laws | | `census` | 36 compiler files; 562 declarations; 40 feature classes | | `lint:verify` | 127 tests; 8 law-rule wiring controls; no provider contacted | | `nest` | 40/40 frozen outcomes / 174 seed calls; 0 unmet; 386 evaluator and 386 Wasm values; 24 boundaries; 100 enum hashes; 6 mutants / 12 lane kills | | `descent` | 38 rule/legacy plus 2 resource seed fixtures; 228 plus 12 phase observations; 20 accepted programs; 24 boundary observations; 7 mutants / 14 lane kills | | `gates:verify` | 18 wrapper tests; 6 semantic mutants |
- docs/compiler-campaign/DESCENT-2.md: | Gate | Passed coverage | | --- | --- | | `frontend` | 14 parser fixtures / 28 observations; 24 boundaries; 4 mutants; 12 classification fixtures / 24 lane observations / 72 downstream observations; 7 classification mutants; 4 boundary and 6 classification laws | | `checker` | 49 fixtures / 98 observations; 10 depth probes; 16 catalog-bound observations; 7 mutants | | `structural` | 16 fixtures / 64 catalog/compiler observations; 4 boundary pairs; 7 mutants | | `fields` | 40 fixtures / 240 phase observations; 36 budgets; 6 host probes; 12 level/inspection observations; 9 mutants | | `wasm` | 25 programs / 90 reference calls in 2 lanes; 62 rejection pairs; 44 boundaries; 7 mutants | | `wasm-trust` | 3 entries; 0 proof holes | | `fields-trust` | 4 entries; 0 proof holes | | `structural-trust` | 2 entries; 0 proof holes | | `owned-store` | 3,532 cases in 2 lanes; 15 literal witnesses; 6 mutants | | `flat-store` | 13,621 observations, 3,534 instances, 2 installed boundary states and 7 lifecycle checks per lane; 2 lanes; 9 mutants | | `recursion` | 19 fixtures / 114 phase observations; 4 fuel probes; 3 mutants | | `fields-wasm` | 8 fixtures / 32 seed calls; 64 evaluator and 64 Node observations; 50 enum byte checks; 30 boundaries; 4 mutants / 8 lane kills; 5 new checked laws | | `census` | 36 compiler files; 562 declarations; 40 feature classes | | `lint:verify` | 127 tests; 8 law-rule wiring controls; no provider contacted | | `nest` | 40/40 frozen outcomes / 174 seed calls; 0 unmet; 386 evaluator and 386 Wasm values; 24 boundaries; 100 enum hashes; 6 mutants / 12 lane kills | | `descent` | 38 rule/legacy plus 2 resource seed fixtures; 228 plus 12 phase observations; 20 accepted programs; 24 boundary observations; 7 mutants / 14 lane kills | | `gates:verify` | 18 wrapper tests; 6 semantic mutants | The complete normalized runner summary, completion lines, source identities and measured times are retained in [`verification.json`](../../tests/compiler-descent/receipts/verification.json).
- docs/compiler-campaign/DESCENT-2.md: Each is killed by the frozen semantic observation in both native and Bun lanes: 14 kills.
- docs/compiler-campaign/DESCENT-2.md: A type error, harness timeout, resource exhaustion or host failure cannot count as a semantic kill.

# Evidence
`tests/compiler-descent/check.py:248-295` function `mutants`:
```python
  248  def mutants(record, cases, mutations):
  249      by_name = {case['name']: case for case in cases}
  250      require(isinstance(mutations, list) and mutations, 'A nonempty mutation list is required')
  251      require(len({mutation['name'] for mutation in mutations}) == len(mutations), 'Duplicate mutant names')
  252      for mutation in mutations:
  253          name = mutation['name']
  254          require(re.fullmatch(r'[a-z][a-z0-9_-]*', name), ('mutant directory name', name))
  255          require(Path(mutation['file']).name == mutation['file'] and mutation['file'].endswith('.bend'),
  256                  ('mutant source path', name))
  257          require(mutation['old'] and mutation['old'] != mutation['new'], ('empty mutation', name))
  258          require(mutation['witness'] in by_name, ('unknown witness', name))
  259          require(mutation['wrong']['exit'] in (0, 2, 3),
  260                  ('mutation witness must be semantic, not exhaustion or host failure', name))
  261          directory = BUILD / name
  262          directory.mkdir(exist_ok=True)
  263          for stale in directory.glob('*.bend'):
  264              stale.unlink()
  265          for source in sorted((ROOT / 'src').glob('*.bend')):
  266              copied = directory / source.name
  267              shutil.copy2(source, copied)
  268              require(digest(copied) == record['inputs'][str(source.relative_to(ROOT))],
  269                      ('source changed before mutation', name, source.name))
  270          target = directory / mutation['file']
  271          original = target.read_text()
  272          require(original.count(mutation['old']) == 1, ('mutation anchor is not unique', name))
  273          target.write_text(original.replace(mutation['old'], mutation['new'], 1))
  274          entry = directory / 'check-cli.bend'
  275          case = by_name[mutation['witness']]
  276          item = {**mutation, 'mutated_sha256': digest(target), 'expected': case['check'], 'lanes': {}}
  277          record['mutants'].append(item)
  278          item['typecheck'] = run([*SEED, entry, '--check-only'])
  279          line(item['typecheck'], 'All terms check.')
  280          for lane, suffix, runtime in LANES:
  281              output = directory / ('mutant' + suffix)
  282              output.unlink(missing_ok=True)
  283              actual = item['lanes'][lane] = {'build': run([*SEED, entry, '-o', output])}
  284              successful(actual['build'])
  285              require(output.is_file() and output.stat().st_size > 0, ('missing mutant build', name, lane))
  286              actual['build_sha256'] = digest(output)
  287              actual['observation'] = run([*runtime, output, ROOT / case['file']])
  288              observe(actual['observation'], mutation['wrong'], 'check')
  289              try:
  290                  observe(actual['observation'], case['check'], 'check')
  291              except AssertionError as error:
  292                  actual['frozen_assertion'] = str(error)
  293                  actual['outcome'] = 'semantic-kill'
  294              else:
  295                  raise AssertionError(('mutant survived frozen assertion', name, lane, actual))
```

`tests/compiler-descent/check.py:334-372` function `counts`:
```python
  334  def counts(record):
  335      observations = [(phase, result) for item in record['fixtures']
  336                      for lane in item['lanes'].values() for phase, result in lane.items()
  337                      if phase in PHASES]
  338      resources = record['resources']
  339      resource_observations = [(phase, result) for item in resources
  340                               for lane in item['lanes'].values() for phase, result in lane.items()
  341                               if phase in PHASES]
  342      return {'seed_fixtures': record['reference']['observations'],
  343              'resource_seed_fixtures': record['resource_reference']['observations'],
  344              'resource_accepted_books': sum(item['expected']['check']['exit'] == 0 for item in resources),
  345              'resource_phase_observations': len(resource_observations),
  346              'resource_evaluation_values': sum(phase == 'eval' and result['exit'] == 0
  347                                                for phase, result in resource_observations),
  348              'resource_wasm_values': sum('wasm' in lane for item in resources for lane in item['lanes'].values()),
  349              'resource_module_hash_pairs': sum(item.get('module_bytes_equal', False) for item in resources),
  350              'resource_preserved_artifacts': sum(lane.get('artifact_preserved', False)
  351                                                  for item in resources for lane in item['lanes'].values()),
  352              'new_fixtures': sum(item['group'] == 'fixtures' for item in record['fixtures']),
  353              'legacy_fixtures': sum(item['group'] == 'legacy' for item in record['fixtures']),
  354              'accepted_books': sum(item['expected']['check']['exit'] == 0 for item in record['fixtures']),
  355              'phase_observations': len(observations),
  356              'check_observations': sum(phase == 'check' for phase, _ in observations),
  357              'evaluation_values': sum(phase == 'eval' and result['exit'] == 0 for phase, result in observations),
  358              'wasm_values': sum('wasm' in lane for item in record['fixtures'] for lane in item['lanes'].values()),
  359              'wasm_observer_links': sum('wasm_observer' in lane for item in record['fixtures'] for lane in item['lanes'].values()),
  360              'module_hash_pairs': sum(item.get('module_bytes_equal', False) for item in record['fixtures']),
  361              'rejected_phase_observations': sum(result['exit'] != 0 for _, result in observations),
  362              'preserved_artifacts': sum(lane.get('artifact_preserved', False)
  363                                         for item in record['fixtures'] for lane in item['lanes'].values()),
  364              'bounds_cases': len(record['bounds']),
  365              'bounds_observations': sum(len(item['lanes']) for item in record['bounds']),
  366              'bounds_exhaustions': sum(result['exit'] == 4 for item in record['bounds']
  367                                        for result in item['lanes'].values()),
  368              'bounds_internal_failures': sum(result['exit'] == 6 for item in record['bounds']
  369                                              for result in item['lanes'].values()),
  370              'proofs': len(record['proofs']), 'mutants': len(record['mutants']),
  371              'semantic_kills': sum(lane.get('outcome') == 'semantic-kill'
  372                                    for item in record['mutants'] for lane in item['lanes'].values())}
```

`tests/compiler-descent/check.py:375-423` function `main`:
```python
  375  def main():
  376      BUILD.mkdir(parents=True, exist_ok=True)
  377      RECEIPT.parent.mkdir(parents=True, exist_ok=True)
  378      record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'incomplete',
  379                'profile': 'knot-fields-wasm-1', 'builds': [], 'proofs': [], 'fixtures': [],
  380                'mutants': [], 'bounds': [], 'resources': []}
  381      try:
  382          manifest = json.loads((HERE / 'expectations.json').read_text())
  383          cases = validate_manifest(manifest)
  384          mutations = json.loads((HERE / 'mutants.json').read_text())
  385          record['inputs'] = hashes(input_paths(manifest))
  386          record['seed_revision'] = manifest['seed_revision']
  387          verify_reference(record, cases)
  388          resources = resource_cases(record)
  389          require(not {case['name'] for case in cases}.intersection(case['name'] for case in resources),
  390                  'Resource case names overlap the original manifest')
  391          record['tools'] = {}
  392          for tool in ('bun', 'node', 'python3'):
  393              record['tools'][tool] = successful(run([tool, '--version']))['stdout'].strip()
  394          require(record['tools']['node'] == 'v22.22.3' and record['tools']['bun'] == '1.3.14', record['tools'])
  395          for proof in ('src/descent-PROOF.bend', 'src/recursion-PROOF.bend'):
  396              item = {'file': proof, 'result': run([*SEED, ROOT / proof])}
  397              record['proofs'].append(item)
  398              line(item['result'], 'All terms check.')
  399          lanes = build_lanes(record)
  400          fixtures(record, manifest, cases, lanes)
  401          # A short harness limit prevents an expansion regression from running unchecked.
  402          # A timeout fails this gate; it is never a matched language diagnostic.
  403          fixtures(record, {'fixtures': resources}, resources, lanes, target='resources', timeout=2)
  404          bounds(record)
  405          mutants(record, cases, mutations)
  406          validate_manifest(manifest)
  407          require(hashes(input_paths(manifest)) == record['inputs'], 'Inputs changed during gate')
  408          record['inputs_unchanged'] = True
  409          record['counts'] = counts(record)
  410          record['status'] = 'passed'
  411      except Exception as error:
  412          record['status'] = 'failed'
  413          record['failure'] = repr(error)
  414          raise
  415      finally:
  416          RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
  417      total = record['counts']
  418      print(f"Descent gate passed: {total['seed_fixtures']} seed fixtures, "
  419            f"{total['accepted_books']} accepted books, {total['phase_observations']} phase observations; "
  420            f"{total['evaluation_values']} evaluator values, {total['wasm_values']} Wasm values; "
  421            f"{total['resource_seed_fixtures']} resource fixtures / {total['resource_phase_observations']} phases; "
  422            f"{total['bounds_observations']} bounds observations; "
  423            f"{total['mutants']} mutants / {total['semantic_kills']} semantic kills")
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

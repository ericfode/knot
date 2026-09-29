<!-- prechecks packet v1; rule=kill-is-semantic; increment=generics; head=78c4942e642a; base=cc9f2fd23d59; builder=scripts/prechecks/packets@3a2ef420dff1; sources: tests/compiler-generics/check.py@78c4942e sha256=c52d6f7f98c727e6ce7930d005ef6aa5208c8d8a8f57a5e9a3177cd6bfe3b465 -->
# Claim
Statements about what counts as a kill:

- tests/compiler-generics/LAW_REVIEW.md: Mutants are independently seed-typechecked; host failures, internal errors, exhaustion and invalid Wasm are not semantic kills.
- tests/compiler-generics/README.md: A parser failure, host/internal error, exhausted budget or invalid Wasm cannot count as a semantic kill.
- tests/compiler-generics/README.md: With the proposal applied, the generics gate reports 73 fixtures, 168 seed calls, 284 evaluator and 284 Node agreements, 270 negative phase observations, 90 preserved artifacts, 28 byte-identical module pairs, 10 ABI arity observations, 3 proof entries and 5 mutants killed in both lanes.
- tests/compiler-generics/README.md: | Gate | Exact completed coverage | | --- | --- | | Frontend — failed | 14 reference fixtures; 28 parser observations; 24 boundaries; 4 mutants; then obsolete generic pin | | Checker | 49 fixtures; 98 observations; 10 depth probes; 16 catalog-bound observations; 7 mutants | | Structural | 16 fixtures; 64 observations; 4 boundary pairs; 7 mutants | | Fields | 40 fixtures; 240 observations; 36 budget probes; 6 host probes; 12 level/inspection observations; 9 mutants | | Wasm | 25 fixtures; 90 reference calls in 2 lanes; 64 rejection pairs; 44 boundaries; 7 mutants | | Wasm trust | 3 entries; 0 proof holes | | Fields trust | 4 entries; 0 proof holes | | Structural trust | 2 entries; 0 proof holes | | Owned-store | 3,532 cases in 2 lanes; 15 literal witnesses; 6 mutants | | Flat-store | Per lane: 13,621 observations, 3,534 instances, 2 installed boundary states, 7 lifecycle checks; 2 lanes; 9 mutants | | Recursion | 19 fixtures; 114 phase observations; 4 fuel probes; 3 mutants | | Fields Wasm | 8 fixtures; 32 seed calls; 64 evaluator and 64 Node observations; 50 frozen enum-byte checks; 30 boundaries; 4 mutants in both lanes | | Census | 39 source files; 677 declarations; 41 feature classes | | Lint verification | 127 tests; 8 law-rule wiring controls | | Generics | 66 fixtures; 165 seed calls; 278 evaluator and 278 Node agreements; 234 negative-phase observations; 78 preserved artifacts; 27 byte-identical module pairs; 10 ABI arity observations; 3 proof entries; 4 mutants / 8 lane kills |

# Evidence
`tests/compiler-generics/check.py:283-355` function `mutation`:
```python
  283  def mutation(spec, rows, controls, sources=None):
  284      name, phase = spec['name'], spec['phase']
  285      require(phase in ('check', 'eval', 'wasm', 'abi'), (name, 'mutation phase'))
  286      row = rows[spec['witness']]
  287      directory = BUILD / name
  288      directory.mkdir(exist_ok=True)
  289      for source in (sources or ROOT / 'src').glob('*.bend'):
  290          shutil.copy2(source, directory / source.name)
  291      target = directory / spec['file']
  292      original = target.read_text()
  293      require(original.count(spec['old']) == 1, (name, 'mutation anchor is not unique'))
  294      target.write_text(original.replace(spec['old'], spec['new']))
  295      if phase in ('wasm', 'abi'):
  296          entry = directory / 'fields-compile.bend'
  297          entry.write_text(COMPILE.read_text().replace('../../src/', './'))
  298      else:
  299          entry = directory / f'{phase}-cli.bend'
  300      typecheck = successful([*SEED, entry, '--check-only'])
  301      require(typecheck['stdout'] == 'All terms check.\n', typecheck)
  302      record = {**spec, 'source_sha256': digest(target), 'typecheck': typecheck, 'lanes': {}}
  303      call, selected = None, None
  304      if phase == 'abi':
  305          selected = [control for control in controls if control['case'] == spec['witness']
  306                      and control['export'] in spec['exports']]
  307          require(len(selected) == len(spec['exports']), (name, 'ABI witness must be frozen'))
  308          record['expected'] = selected
  309      elif phase != 'check':
  310          calls = [call for call in row['reference']['calls'] if call['entry'] == spec['entry']
  311                   and call['ordinals'] == spec['ordinals']]
  312          require(len(calls) == 1, (name, 'mutant witness must be one frozen call'))
  313          call = calls[0]
  314          record['expected'] = call['result']
  315      else:
  316          record['expected'] = row['case']['knot']
  317      for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
  318          executable = directory / ('mutant' + suffix)
  319          built = successful([*SEED, entry, '-o', executable], timeout=120)
  320          command = [*runtime, executable]
  321          item = {'build': built, 'sha256': digest(executable)}
  322          if phase == 'check':
  323              actual = run([*command, row['source']])
  324          elif phase == 'eval':
  325              actual = run([*command, row['source'], call['entry'], 1048576, *call['ordinals']])
  326          else:
  327              output = directory / f'{lane}.wasm'
  328              output.write_bytes(MARKER)
  329              item['compile'] = run([*command, row['source'], output])
  330              compiled(item['compile'], output)
  331              if phase == 'abi':
  332                  actual = run(['node', ABI_HOST, output, *spec['exports']])
  333              else:
  334                  actual = run(['node', HOST, PROFILE, output, call['entry'], *call['ordinals']])
  335          item['actual'] = actual
  336          observe_literal(actual, spec['actual'])
  337          require(actual['exit'] in (0, 2, 3), (name, 'host failure or exhaustion is not a semantic kill'))
  338          try:
  339              if phase == 'check':
  340                  if row['case']['knot']['require'] == 'agree':
  341                      checked(actual)
  342                  else:
  343                      rejection(actual, row['case']['knot'])
  344              elif phase == 'eval':
  345                  evaluated(actual, call)
  346              elif phase == 'wasm':
  347                  wasm_result(actual, call, output)
  348              else:
  349                  abi_result(actual, selected, output)
  350          except AssertionError:
  351              item['outcome'] = 'semantic-kill'
  352          else:
  353              raise AssertionError((name, lane, 'mutant survived'))
  354          record['lanes'][lane] = item
  355      return record
```

`tests/compiler-generics/check.py:358-383` function `coverage`:
```python
  358  def coverage(record):
  359      fixtures = record['fixtures']
  360      lane_rows = [lane for row in fixtures for lane in row['lanes'].values()]
  361      return {
  362          'fixtures': len(fixtures), 'seed_calls': sum(row['seed_calls'] for row in fixtures),
  363          'seed_valid': sum(row['requirement']['require'] != 'reject' for row in fixtures),
  364          'seed_invalid': sum(row['requirement']['require'] == 'reject' for row in fixtures),
  365          'agreed_fixtures': sum(row['status'] == 'agreed' for row in fixtures),
  366          'rejected_fixtures': sum(row['status'] == 'rejected' for row in fixtures),
  367          'unsupported_fixtures': sum(row['status'] == 'unsupported' for row in fixtures),
  368          'blocked_fixtures': sum(row['status'] == 'blocked' for row in fixtures),
  369          'check_observations': len(lane_rows), 'compile_observations': len(lane_rows),
  370          'evaluator_agreements': sum(call.get('evaluator_agreed', False)
  371                                      for row in lane_rows for call in row['calls']),
  372          'wasm_agreements': sum(call.get('wasm_agreed', False)
  373                                for row in lane_rows for call in row['calls']),
  374          'negative_phase_observations': 3 * sum('eval' in row for row in lane_rows),
  375          'preserved_artifacts': sum(row.get('artifact_preserved', False) for row in lane_rows),
  376          'byte_identical_modules': sum(row.get('module_bytes_identical', False) for row in fixtures),
  377          'abi_module_probes': len(record['abi']),
  378          'abi_arity_observations': sum(len(row['controls']) for row in record['abi']),
  379          'execution_lanes': len({lane for row in fixtures for lane in row['lanes']}),
  380          'proof_entries': len(record['proofs']),
  381          'mutants': len(record['mutants']),
  382          'mutant_lane_kills': sum(len(row['lanes']) for row in record['mutants']),
  383      }
```

`tests/compiler-generics/check.py:386-449` function `main`:
```python
  386  def main():
  387      BUILD.mkdir(parents=True, exist_ok=True)
  388      RECEIPT.parent.mkdir(exist_ok=True)
  389      record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
  390                'status': 'incomplete', 'profile': 'knot-generics-1',
  391                'fixtures': [], 'proofs': [], 'mutants': [], 'abi': []}
  392      try:
  393          inputs = [*sorted((ROOT / 'src').glob('*.bend')), ROOT / 'src/SPEC.md',
  394                    ROOT / 'src/CONTRACT.json', HOST, COMPILE, ABI_EXPECTATIONS, Path(__file__)]
  395          for directory in SOURCES:
  396              inputs += [directory / 'expectations.json', directory / 'regen.py',
  397                         *sorted((directory / 'fixtures').glob('*.bend'))]
  398          record['inputs'] = {str(path.relative_to(ROOT)): digest(path) for path in inputs}
  399          record['tools'] = {tool: successful([tool, '--version'])['stdout'].strip()
  400                             for tool in ('bun', 'node', 'python3', 'wasm2wat')}
  401          record['reference'] = [successful(['python3', directory / 'regen.py']) for directory in SOURCES]
  402          rows = corpus()
  403          controls = abi_controls(rows)
  404          ABI_HOST.write_text(ABI_SOURCE)
  405          record['abi_host_sha256'] = digest(ABI_HOST)
  406          record['seed_revision'] = json.loads((HERE / 'expectations.json').read_text())['seed']['revision']
  407          for proof in PROOFS:
  408              result = successful([*SEED, ROOT / proof])
  409              require(result['stdout'] == 'All terms check.\n', result)
  410              record['proofs'].append({'entry': proof, 'result': result})
  411          record['builds'], lanes = [], {}
  412          for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
  413              lanes[lane] = {}
  414              for phase in ('check', 'eval', 'compile'):
  415                  entry = COMPILE if phase == 'compile' else ROOT / f'src/{phase}-cli.bend'
  416                  executable = BUILD / (phase + suffix)
  417                  built = successful([*SEED, entry, '-o', executable], timeout=120)
  418                  record['builds'].append({'lane': lane, 'phase': phase,
  419                                           'result': built, 'sha256': digest(executable)})
  420                  lanes[lane][phase] = [*runtime, executable]
  421          for row in rows:
  422              record['fixtures'].append(fixture(row, lanes))
  423          failed = [(row['name'], row['status']) for row in record['fixtures']
  424                    if row['status'] not in ('agreed', 'rejected', 'unsupported')]
  425          require(not failed, ('fixture failures', failed))
  426          record['abi'] = abi_observations(controls, lanes)
  427          require({spec['name'] for spec in MUTANTS} == MUTANT_NAMES and len(MUTANTS) == len(MUTANT_NAMES),
  428                  'The five required semantic mutants must be configured exactly once')
  429          indexed = {row['case']['name']: row for row in rows}
  430          for spec in MUTANTS:
  431              record['mutants'].append(mutation(spec, indexed, controls))
  432          require(all(digest(ROOT / path) == expected for path, expected in record['inputs'].items()),
  433                  'Inputs changed during gate')
  434          record['status'] = 'passed'
  435      except Exception as error:
  436          record['failure'] = repr(error)
  437          raise
  438      finally:
  439          record['counts'] = coverage(record)
  440          RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
  441      counts = record['counts']
  442      print(f"Generics gate passed: {counts['fixtures']} fixtures, {counts['seed_calls']} seed calls, "
  443            f"{counts['evaluator_agreements']} evaluator and {counts['wasm_agreements']} Node agreements, "
  444            f"{counts['negative_phase_observations']} negative phase observations, "
  445            f"{counts['preserved_artifacts']} preserved artifacts, "
  446            f"{counts['byte_identical_modules']} byte-identical module pairs, "
  447            f"{counts['abi_arity_observations']} independent ABI arity observations, "
  448            f"{counts['proof_entries']} complete proof entries, "
  449            f"{counts['mutants']} type-correct mutants killed in both lanes. {RECEIPT}")
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

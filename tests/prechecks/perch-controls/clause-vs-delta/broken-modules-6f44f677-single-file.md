<!-- prechecks packet v1; rule=clause-vs-delta; increment=modules; head=6f44f6774d90; base=92de61cea385; builder=scripts/prechecks/packets@47dbd98ca1c7; sources: src/CONTRACT.json@6f44f677 sha256=bea1e2e42976648448cb2369a226d7e38eaf6d6803092c1ad78af9d500ae3dad; src/base-pin-PROOF.bend@6f44f677 sha256=eeaf454f5623a6252f5ff9afcd857f5802e6f1a725a995e9ace367f2462096a3; tests/compiler-modules/check.py@6f44f677 sha256=750abd65ea77809397515c968afafed1e0cd0061ae35f947fe9a349b8c11b394 -->
# Claim
Invariance clause (src/CONTRACT.json):

> The compiler opens the requested output only after complete checking and bounded emission; semantic failure and exhaustion leave existing output untouched. File-write failures are HostFailure and may leave an incomplete file, never a Built result. Callers must use the exit status, not file presence, as evidence of a fresh artifact.

# Evidence
Evidence: the governed diff hunks (base to head).
```
`src/base-pin-PROOF.bend:11-11` (added)
   11  def L.complete_block_still_gets_padding(): {==}

`tests/compiler-modules/check.py:287-302` (added)
  287  def build_lanes(record):
  288      lanes = {}
  289      record['builds'] = []
  290      for lane, suffix, runtime in [('native', '', []), ('bun', '.js', ['bun'])]:
  291          lanes[lane] = {}
  292          for phase in ('check', 'eval', 'compile'):
  293              output = BUILD / (phase + suffix)
  294              output.unlink(missing_ok=True)
  295              built = successful([*SEED, ROOT / f'src/{phase}-cli.bend', '-o', output])
  296              record['builds'].append({'lane': lane, 'phase': phase, 'result': built,
  297                                       'sha256': digest(output)})
  298              lanes[lane][phase] = [*runtime, output, '--bundle', BUNDLE]
  299              lanes[lane]['plain-' + phase] = [*runtime, output]
  300              if phase == 'check':
  301                  lanes[lane]['audit'] = [*runtime, output, '--audit-bundle', BUNDLE]
  302      return lanes

`tests/compiler-modules/check.py:305-325` (added)
  305  def tampered_base(lanes, expected):
  306      # Exercise the real loader against a private corrupted Base. The pinned
  307      # seed, frozen bundle and compiler sources remain untouched.
  308      cwd = BUILD / 'tampered-base-root'
  309      target = cwd / expected['base']['path']
  310      target.parent.mkdir(parents=True, exist_ok=True)
  311      target.write_bytes((ROOT / expected['base']['path']).read_bytes() + b'\n')
  312      source = HERE / 'fixtures/base-bool.bend'
  313      records = []
  314      for lane, commands in lanes.items():
  315          for phase in ('check', 'eval', 'compile'):
  316              output = BUILD / f'tampered-{lane}.wasm'
  317              marker = b'existing artifact survives Base pin failure\n'
  318              output.write_bytes(marker)
  319              extra = [] if phase == 'check' else ['main', 65536] if phase == 'eval' else [output]
  320              result = run([*commands[phase], source, *extra], cwd=cwd)
  321              rejection(result, 5, 'HostFailure\tload\tbase-pin')
  322              require(output.read_bytes() == marker, ('Base pin failure changed output', result))
  323              records.append({'lane': lane, 'phase': phase, 'result': result,
  324                              'artifact_preserved': phase == 'compile'})
  325      return records

`tests/compiler-modules/check.py:396-469` (added)
  396  def fixture_observations(fixture, lanes, base):
  397      name = fixture.get('name', Path(fixture['file']).stem)
  398      source = HERE / fixture['file']
  399      if fixture.get('entry_mode') == 'relative':
  400          source = source.relative_to(ROOT)
  401      bundle = HERE / fixture.get('bundle', 'bundle/lib')
  402      if fixture.get('bundle_mode') == 'relative':
  403          bundle = bundle.relative_to(ROOT)
  404      item = {'name': name, 'file': fixture['file'], 'knot': fixture['knot'],
  405              'reference': fixture['calls'], 'lanes': {}}
  406      outputs = {}
  407      for lane, commands in lanes.items():
  408          plain = {phase: commands['plain-' + phase] for phase in ('check', 'eval', 'compile')}
  409          commands = {phase: [*argv[:-1], bundle] for phase, argv in commands.items() if '-' not in phase}
  410          checked = run([*commands['check'], source])
  411          if observe(checked, fixture):
  412              require(checked['stdout'].startswith('Checked\n'), checked)
  413          evaluated = []
  414          for call in fixture['calls']:
  415              args = [arg['tag'] for arg in call['arguments']]
  416              result = run([*commands['eval'], source, call['export'], 65536, *args])
  417              entry = {'export': call['export'], 'arguments': call['arguments'], 'result': result}
  418              if observe(result, fixture):
  419                  entry['value'] = value(result, call)
  420              evaluated.append(entry)
  421          output = BUILD / f'{name}-{lane}.wasm'
  422          marker = b'existing output must survive rejected module compilation\n'
  423          output.write_bytes(marker)
  424          compiled = run([*commands['compile'], source, output])
  425          accepted = observe(compiled, fixture)
  426          evidence = {'check': checked, 'evaluations': evaluated, 'compile': compiled,
  427                      'wasm': [], 'artifact_preserved': not accepted}
  428          if checked['exit'] == 0:
  429              evidence['audit'] = audit(run([*commands['audit'], source]), fixture, base)
  430          if accepted:
  431              binary = output.read_bytes()
  432              require(binary.startswith(b'\0asm\x01\0\0\0'), compiled)
  433              require(compiled['stdout'].strip() == f'Built\t{len(binary)}', compiled)
  434              evidence['sha256'] = digest(output)
  435              outputs[lane] = binary
  436              for call in fixture['calls']:
  437                  args = [arg['tag'] for arg in call['arguments']]
  438                  result = successful(['node', HOST, output, call['export'], *args])
  439                  answer = json.loads(result['stdout'])
  440                  require(answer == {'validated': True, 'export': call['export'],
  441                                     'arguments': args, 'result': call['tag'],
  442                                     'bytes': len(binary)}, (call, result))
  443                  evidence['wasm'].append({'export': call['export'], 'arguments': args,
  444                                           'expected_tag': call['tag'], 'result': result})
  445          else:
  446              require(output.read_bytes() == marker, ('rejection changed output', compiled))
  447          if 'plain' in fixture:
  448              evidence['plain'] = single_file(fixture, plain, source, name, lane)
  449          item['lanes'][lane] = evidence
  450      native, bun = item['lanes']['native'], item['lanes']['bun']
  451      for phase in ('check', 'compile'):
  452          require(observation(native[phase]) == observation(bun[phase]),
  453                  (fixture['file'], phase, 'native/Bun observations differ', native[phase], bun[phase]))
  454      require([observation(row['result']) for row in native['evaluations']] ==
  455              [observation(row['result']) for row in bun['evaluations']],
  456              (fixture['file'], 'native/Bun evaluation differs'))
  457      if 'plain' in fixture:
  458          require([observation(r) for r in native['plain'].values()] ==
  459                  [observation(r) for r in bun['plain'].values()],
  460                  (fixture['file'], 'native/Bun single-file observations differ'))
  461      if 'audit' in native:
  462          require('audit' in bun and
  463                  observation(native['audit']['result']) == observation(bun['audit']['result']),
  464                  (fixture['file'], 'native/Bun trust inventories differ'))
  465      if outputs:
  466          require(set(outputs) == {'native', 'bun'} and outputs['native'] == outputs['bun'],
  467                  (fixture['file'], 'native/Bun Wasm bytes differ'))
  468          item['byte_identical'] = True
  469      return item

`tests/compiler-modules/check.py:670-736` (added)
  670  def main():
  671      BUILD.mkdir(parents=True, exist_ok=True)
  672      RECEIPT.parent.mkdir(parents=True, exist_ok=True)
  673      manifest = json.loads((HERE / 'expectations.json').read_text())
  674      paths = [*sorted((ROOT / 'src').glob('*.bend')), ROOT / 'src/SPEC.md',
  675               ROOT / 'src/CONTRACT.json', HOST, Path(__file__), HERE / 'expectations.json',
  676               HERE / 'FIXTURES.md', HERE / 'regen.py', HERE / 'regressions.json',
  677               HERE / 'host-check-expectations.json',
  678               HERE / 'probes.json', HERE / 'pin.bend', HERE / 'pin-expectations.json',
  679               HERE / 'review-round2.json', HERE / 'review-round3.json', *sorted((ROOT / 'src/host').glob('*')),
  680               ROOT / 'tests/compiler-io-abi-2/expectations.json',
  681               *sorted((ROOT / 'tests/compiler-io-abi-2/reference').glob('*'))]
  682      paths += [p for folder in ('fixtures', 'calls', 'bundle', 'regressions', 'probes', 'review-round2', 'review-round3')
  683                for p in sorted((HERE / folder).rglob('*')) if p.is_file()]
  684      record = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
  685                'status': 'incomplete', 'seed': manifest['seed'],
  686                'inputs': {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}}
  687      try:
  688          record['reference_verification'] = successful(['python3', HERE / 'regen.py'])
  689          supplemental, record['supplemental_reference'] = supplemental_reference(manifest)
  690          probes, record['probe_reference'] = probe_reference(manifest)
  691          review, record['review_reference'] = review_reference(manifest, 'review-round2')
  692          round3, record['round3_reference'] = review_reference(manifest, 'review-round3')
  693          review += round3
  694          record['adapters'] = adapter_pins()
  695          record['tools'] = {tool: successful([tool, '--version'])['stdout'].strip()
  696                             for tool in ('bun', 'node', 'python3')}
  697          require(record['tools']['node'] == 'v22.22.3', record['tools'])
  698          record['base_reference'] = base_reference(manifest)
  699          record['proofs'] = []
  700          for entry in PROOFS:
  701              result = successful([*SEED, ROOT / entry])
  702              require(result['stdout'].strip() == 'All terms check.', result)
  703              record['proofs'].append({'entry': entry, 'result': result})
  704          lanes = build_lanes(record)
  705          pin_controls(record)
  706          record['tampered_base'] = tampered_base(lanes, json.loads((HERE / 'pin-expectations.json').read_text()))
  707          record['fixtures'] = []
  708          for fixture in [*manifest['fixtures'], *supplemental, *probes, *review]:
  709              record['fixtures'].append(fixture_observations(fixture, lanes, record['base_reference']))
  710          record['mutants'] = mutants([*manifest['fixtures'], *review])
  711          require(all(digest(ROOT / path) == identity for path, identity in record['inputs'].items()),
  712                  'Inputs changed during modules gate')
  713          seed_dir = ROOT / '.toolchain/bend-2.0.29-574b6d3/bend2'
  714          require(all(digest(seed_dir / name) == identity
  715                      for name, identity in manifest['seed']['sha256'].items()),
  716                  'Pinned seed changed during modules gate')
  717          record['status'] = 'passed'
  718      except Exception as error:
  719          record['failure'] = repr(error)
  720          raise
  721      finally:
  722          RECEIPT.write_text(json.dumps(record, indent=2) + '\n')
  723      fixtures = record['fixtures']
  724      lane_records = [lane for fixture in fixtures for lane in fixture['lanes'].values()]
  725      calls = sum(len(fixture['reference']) for fixture in fixtures)
  726      evaluations = sum(len(lane['evaluations']) for lane in lane_records)
  727      wasm = sum(len(lane['wasm']) for lane in lane_records)
  728      preserved = sum(lane['artifact_preserved'] for lane in lane_records)
  729      pairs = sum(fixture.get('byte_identical', False) for fixture in fixtures)
  730      audits = sum('audit' in lane for lane in lane_records)
  731      print(f'Modules gate passed: {len(fixtures)} fixtures, {calls} seed calls, '
  732            f'{len(lane_records)} checks, {evaluations} evaluations, {len(lane_records)} compilations, '
  733            f'{wasm} Wasm observations, {pairs} byte-identity pairs, '
  734            f'{preserved} preserved outputs, {audits} trust audits, '
  735            f'{len(record["pin"])} pin observations, {len(record["tampered_base"])} tampered-Base observations, '
  736            f'{len(record["mutants"])} semantic mutants')
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

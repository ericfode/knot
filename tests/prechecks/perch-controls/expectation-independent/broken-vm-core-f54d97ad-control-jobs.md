<!-- prechecks packet v1; rule=expectation-independent; increment=vm-core; head=f54d97ad3397; base=0f511b06ba24; builder=scripts/prechecks/packets@40e325337e4a; sources: vm/check-core.py@f54d97ad sha256=a00f30eb545d00e7ebf1b31552e65dc23b5a6a9b0250cd2a1d46ff7b59e37c97 -->
# Claim
Statements about where expected values come from:

- docs/compiler-campaign/GATES.md: The test build confirms each exhaustion cause and audits the state after every transition. - `vm/core/fixtures.json` fixes literal-review runs, state-dump rows and lowered limits, including the 250,000-deep non-tail recursion. - A 200,000-deep nested expression runs on a 64 KiB host stack. - The 61 malformed-image controls and a seeded fuzz corpus of 3,120 mutated goldens are refused with the reference codec's first defect, and none traps. - Nine WAT mutants are each killed by a wrong observation.
- vm/CORE.md: `vm/vm.wat` implements [SPEC.md](SPEC.md) as written, independently of `vm/model.bend`; the two are compared in `vm-lockstep`.
- vm/CORE.md: A refusal therefore names the reference codec's first defect.
- vm/CORE.md: The gate requires this on: - the 61 frozen controls; - 3,120 seeded single mutations of the goldens: 2,868 refused, and 252 admitted and run to a clean outcome.

# Evidence
`vm/check-core.py:366-570` function `main`, which builds expected values:
```python
  366  def main() -> int:
  367      started = datetime.datetime.now(datetime.timezone.utc)
  368      if BUILD.exists():
  369          shutil.rmtree(BUILD)
  370      BUILD.mkdir(parents=True)
  371      reg = codec.registry()
  372      digest = codec.base_digest(reg)
  373      record = {'date': started.isoformat(), 'status': 'incomplete',
  374                'scope': 'knot-vm-1 vm/vm.wat: loader, validator, machine, describe; vm-core subset of SPEC section 10',
  375                'inputs': {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(
  376                    [HERE / 'vm.wat', HERE / 'vm.wasm', HERE / 'build.json', HERE / 'build.py', HERE / 'harness.mjs',
  377                     HERE / 'check-core.py', HERE / 'SPEC.md', HERE / 'serializer.py', HERE / 'registry.json', HOST,
  378                     HERE / 'golden/vm-expected.json', *(HERE / 'core').glob('*')])}}
  379  
  380      # pins and module shape
  381      pins, module_bytes, test_bytes = build.build()
  382      frozen = json.loads((HERE / 'build.json').read_text())
  383      require(frozen == pins, f'vm/build.json pins differ from a fresh build: {frozen} vs {pins}')
  384      require((HERE / 'vm.wasm').read_bytes() == module_bytes, 'vm/vm.wasm reassembles byte-identically')
  385      module, test = HERE / 'vm.wasm', BUILD / 'vm-test.wasm'
  386      test.write_bytes(test_bytes)
  387      shapes = {'module': module_shape(module), 'test_build': module_shape(test)}
  388      check_shape(shapes['module'], False)
  389      check_shape(shapes['test_build'], True)
  390      record['pins'] = pins
  391      record['shape'] = shapes
  392  
  393      # goldens through the host, then the test build
  394      expected = json.loads((HERE / 'golden/vm-expected.json').read_text())
  395      golden = HERE / 'golden'
  396  
  397      def golden_argv(name):
  398          return [a if a != 'IMAGE' else f'{name}.kimg' for a in expected['cases'][name]['argv']]
  399  
  400      names = sorted(expected['cases'])
  401      results = dict(zip(names, pool(lambda n: host(module, golden, golden_argv(n)), names)))
  402      traced = harness([{'id': n, 'wasm': str(test), 'files': {f'{n}.kimg': str(golden / f'{n}.kimg')},
  403                         'argv': golden_argv(n), 'trace': 'audit'} for n in names])
  404      goldens = []
  405      for name in names:
  406          case, got, dump = expected['cases'][name], results[name], traced[name]
  407          state = dump['state']
  408          require(dump['broken'] is None, f'{name}: state audit {dump["broken"]}')
  409          if 'exit' in case:
  410              require((got['exit'], got['stdout'], got['stderr']) == (case['exit'], case['stdout'], case['stderr']),
  411                      f'{name}: {got} differs from vm-expected')
  412              require(state['outcome'] == 'Completed', f'{name}: dump outcome {state["outcome"]}')
  413          elif case['outcome'] == 'Exhausted':
  414              require(got['exit'] == 4 and got['stderr'] == 'Exhausted\tio\tmemory\n' and not got['stdout'],
  415                      f'{name}: {got}')
  416              require((state['outcome'], state['kind'], state['cause']) == ('Exhausted', case['kind'], case['cause']),
  417                      f'{name}: dump {state}')
  418          else:
  419              require(case['outcome'] == 'Unsupported' and got['exit'] == 3 and not got['stdout'] and
  420                      got['stderr'] == f"Unsupported\t{case['cause'].replace(' ', chr(9))}\n", f'{name}: {got}')
  421              require(state['outcome'] == 'Unsupported', f'{name}: dump {state}')
  422          require((dump['exit'], dump['stdout']) == (got['exit'], got['stdout']), f'{name}: harness and host differ')
  423          goldens.append({'name': name, 'exit': got['exit'], 'stdout_sha256': sha(got['stdout'].encode()),
  424                          'outcome': state['outcome'], 'cause': state['cause'], 'calls': state['calls'],
  425                          'transitions': dump['steps'], 'audited': dump['audited']})
  426      record['goldens'] = goldens
  427  
  428      # vm/core fixtures: literal-review runs, dumps and lowered limits
  429      fixtures = json.loads((HERE / 'core/fixtures.json').read_text())
  430      sandbox = BUILD / 'sandbox'
  431      sandbox.mkdir()
  432  
  433      def staged(image):
  434          if image is None:
  435              return 'missing.kimg'
  436          name = image.replace('/', '-') + '.kimg'
  437          if not (sandbox / name).exists():
  438              shutil.copy(HERE / f'{image}.kimg', sandbox / name)
  439          return name
  440  
  441      runs = fixtures['runs']
  442      for r in runs:
  443          staged(r['image'])
  444      ran = pool(lambda r: host(module, sandbox, [staged(r['image']), *r['argv']]), runs)
  445      core = []
  446      for r, got in zip(runs, ran):
  447          require(got == r['expect'], f"fixture {r['name']}: {got} vs {r['expect']}")
  448          core.append({'name': r['name'], 'exit': got['exit'], 'stdout_sha256': sha(got['stdout'].encode())})
  449      by_name = {r['name']: r for r in runs}
  450      jobs = [{'id': n, 'wasm': str(test), 'files': {staged(by_name[n]['image']): str(sandbox / staged(by_name[n]['image']))},
  451               'argv': [staged(by_name[n]['image']), *by_name[n]['argv']], 'trace': 'yields'} for n in fixtures['dumps']]
  452      jobs += [{'id': l['name'], 'wasm': str(test), 'files': {staged(l['image']): str(sandbox / staged(l['image']))},
  453                'argv': [staged(l['image']), *l['argv']], 'limits': l['limits']} for l in fixtures['limited']]
  454      dumped = harness(jobs)
  455      dumps = []
  456      for name, want in [*fixtures['dumps'].items(), *((l['name'], l['dump']) for l in fixtures['limited'])]:
  457          got, state = dumped[name], dumped[name]['state']
  458          seen = {'outcome': state['outcome'], 'kind': state['kind'], 'cause': state['cause'],
  459                  'calls': state['calls'], 'yields': got['yields']}
  460          require(all(seen[k] == v for k, v in want.items()), f'dump {name}: {seen} vs {want}')
  461          dumps.append({'name': name, **{k: seen[k] for k in want}})
  462      record['fixtures'] = {'runs': core, 'dumps': dumps}
  463  
  464      # nothing recurses: a 200,000-deep nested expression, and the deep runs on a 64 KiB host stack
  465      small = nested_plan(40)
  466      require(nested_image(40, digest) == codec.encode(small, digest), 'the nested generator matches serializer.encode')
  467      deep = nested_image(NEST, digest)
  468      (sandbox / 'nested.kimg').write_bytes(deep)
  469      stack = {}
  470      for label, argv in [('nested-200k', ['nested.kimg', 'main', str(NEST + 2)]),
  471                          ('deep-250k', [staged('core/deep-250k'), 'main', '500003']),
  472                          ('render-list', [staged('core/render-list'), 'main', '1000000'])]:
  473          got = host(module, sandbox, argv, (SMALL_STACK,))
  474          want = by_name.get(label, {}).get('expect') or {'exit': 0, 'stdout': 'Evaluated\t1\t1\tTrue{}\n', 'stderr': ''}
  475          require(got == want, f'{label} under {SMALL_STACK}: {got}')
  476          stack[label] = {'exit': got['exit'], 'stdout_sha256': sha(got['stdout'].encode())}
  477      stack['nested-200k'].update(words=len(deep) // 4, sha256=sha(deep), fuel=NEST + 2)
  478      record['host_stack'] = {'node_flag': SMALL_STACK, 'runs': stack}
  479  
  480      # malformed images: the frozen controls, then a seeded fuzz corpus
  481      plans = {p.name[:-len('.plan.json')]: json.loads(p.read_text()) for p in golden.glob('*.plan.json')}
  482      images = {p.stem: p.read_bytes() for p in golden.glob('*.kimg')}
  483      controls = spec.byte_controls(images, digest) + [
  484          (f'plan:{k}', codec.encode(p, digest), 'HostFailure image: validator: ', m) for k, p, m in spec.plan_controls(plans)]
  485      require(len(controls) == 61, f'61 frozen controls, found {len(controls)}')
  486      malformed = BUILD / 'malformed'
  487      malformed.mkdir()
  488      rows = []
  489      for i, (label, data, _, _) in enumerate(controls):
  490          (malformed / f'c{i}.kimg').write_bytes(data)
  491          entry = int.from_bytes(data[12:16], 'little')
  492          rows.append({'label': label, 'sha256': sha(data), 'reference': spec.rejected(data, reg, digest),
  493                       'argv': [f'c{i}.kimg', '1000', '--'] if entry == 1 else [f'c{i}.kimg', 'main', '1000']})
  494      got = pool(lambda r: host(module, malformed, r['argv']), rows)
  495      dumped = harness([{'id': r['label'], 'wasm': str(test), 'files': {r['argv'][0]: str(malformed / r['argv'][0])},
  496                         'argv': r['argv']} for r in rows])
  497      refused = []
  498      for r, g in zip(rows, got):
  499          want = expected_reason(r['reference'])
  500          g['state'] = dumped[r['label']]['state']
  501          require(clean(g), f"control {r['label']}: {g}")
  502          require(observed_reason(g) == want, f"control {r['label']}: VM {g['stderr']!r}, reference {r['reference']!r}")
  503          refused.append({'control': r['label'], 'reference': r['reference'], 'vm': want, 'exit': g['exit']})
  504      fuzz = BUILD / 'fuzz'
  505      fuzz.mkdir()
  506      corpus = fuzz_corpus(images, reg, digest, fuzz)
  507      fuzzed = harness([{'id': r['label'], 'wasm': str(test), 'files': {r['argv'][0]: str(fuzz / r['argv'][0])},
  508                         'argv': r['argv']} for r in corpus], timeout=1200)
  509      tally = {'refused': 0, 'accepted': 0, 'reference_crash': 0}
  510      for r in corpus:
  511          g = fuzzed[r['label']]
  512          require(clean(g), f"fuzz {r['label']} is not a clean outcome: {g['status']} {g['stderr']!r}")
  513          ref = r['reference']
  514          if ref is None:
  515              require(observed_reason(g) is None, f"fuzz {r['label']}: reference admits it, VM refused {g['stderr']!r}")
  516              tally['accepted'] += 1
  517          elif ref.startswith('reference-crash'):
  518              tally['reference_crash'] += 1
  519          else:
  520              require(observed_reason(g) == expected_reason(ref), f"fuzz {r['label']}: VM {g['stderr']!r}, reference {ref!r}")
  521              tally['refused'] += 1
  522      record['malformed'] = {'controls': refused, 'fuzz': {'seed': FUZZ_SEED, 'per_image': FUZZ_PER_IMAGE,
  523                                                           'images': len(corpus), 'corpus_sha256': sha(json.dumps(
  524                                                               [r['sha256'] for r in corpus]).encode()), **tally}}
  525  
  526      # mutants: a changed observation in their group, never a crash
  527      source = (HERE / 'vm.wat').read_text()
  528      goldens_jobs = [{'id': f'golden:{n}', 'files': {f'{n}.kimg': str(golden / f'{n}.kimg')}, 'argv': golden_argv(n),
  529                       'want': {k: expected['cases'][n][k] for k in ('exit', 'stdout', 'stderr') if k in expected['cases'][n]}
  530                       if 'exit' in expected['cases'][n] else {'exit': results[n]['exit'], 'stdout': '', 'stderr': results[n]['stderr']}}
  531                      for n in names]
  532      fixture_jobs = [{'id': f"fixture:{r['name']}", 'files': {staged(r['image']): str(sandbox / staged(r['image']))} if r['image'] else {},
  533                       'argv': [staged(r['image']), *r['argv']], 'want': r['expect']} for r in runs]
  534      control_jobs = [{'id': f"control:{r['label']}", 'files': {r['argv'][0]: str(malformed / r['argv'][0])},
  535                       'argv': r['argv'], 'want': {'exit': g['exit'], 'stdout': g['stdout'], 'stderr': g['stderr']}}
  536                      for r, g in zip(rows, got)]
  537      groups = {'goldens': goldens_jobs, 'fixtures': fixture_jobs, 'controls': goldens_jobs + control_jobs,
  538                'fuel': [j for j in fixture_jobs if 'fuel' in j['id']],
  539                'quantum': [j for j in fixture_jobs if 'quantum' in j['id']]}
  540      killed = []
  541      for name, breaks, edits, group in MUTANTS:
  542          text = source
  543         
```
[truncated after 12,288 bytes; 2,044 bytes omitted]

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

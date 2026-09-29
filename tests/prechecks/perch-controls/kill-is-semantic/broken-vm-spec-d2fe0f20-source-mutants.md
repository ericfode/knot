<!-- prechecks packet v1; rule=kill-is-semantic; increment=vm-spec; head=d2fe0f2048fb; base=454bf3059679; builder=scripts/prechecks/packets@40e325337e4a; sources: vm/check-spec.py@d2fe0f20 sha256=a24f2a01dc7b977efbdc2e4c76336dc96fa8a07f1f620bbf34db2a2811ba0de1 -->
# Claim
Statements about what counts as a kill:

- docs/COMPILER-CAMPAIGN.md: mutants killed by named gates (definition of done, trusted runtime).

# Evidence
`vm/check-spec.py:700-726` function `codec_mutants`:
```python
  700  def codec_mutants(plans, images, controls, reg, digest) -> list:
  701      source = CODEC.read_text()
  702      results = []
  703      for name, edits in CODEC_MUTANTS:
  704          text = source
  705          for old, new in edits:
  706              require(text.count(old) == 1, f'codec mutant {name} is not uniquely located')
  707              text = text.replace(old, new)
  708          mutant = load_codec(text)
  709          killed_by = None
  710          for case, plan in plans.items():
  711              try:
  712                  if mutant.encode(plan, digest) != images[case]:
  713                      killed_by = f'image {case} differs'
  714                      break
  715              except Exception:
  716                  continue
  717          for label, data, reason, message in [] if killed_by else controls:
  718              try:
  719                  got = rejected(data, reg, digest, mutant)
  720              except Exception:
  721                  continue
  722              if got is None or not got.startswith(reason) or message not in got:
  723                  killed_by = f'control {label}: {got}'
  724                  break
  725          results.append({'mutant': name, 'killed': killed_by is not None, 'by': killed_by})
  726      return results
```

`vm/check-spec.py:736-749` function `source_mutants`:
```python
  736  def source_mutants(cases, built) -> list:
  737      out = []
  738      for name, old, new in SOURCE_MUTANTS:
  739          case = cases[name]
  740          text = (ROOT / case['source']).read_text()
  741          require(text.count(old) == 1, f'source mutant {name}')
  742          path = BUILD / 'mutants' / f'{name}.bend'
  743          path.parent.mkdir(parents=True, exist_ok=True)
  744          path.write_text(text.replace(old, new))
  745          mutated = dict(case, source=path.relative_to(ROOT).as_posix())
  746          got = lanes(mutated, built)
  747          killed = got['seed'] != case['seed'] and got['eval'] != case['eval']
  748          out.append({'mutant': f'source:{name}', 'killed': killed, 'seed': got['seed'], 'eval': got['eval']})
  749      return out
```

`vm/check-spec.py:802-905` function `main`:
```python
  802  def main() -> int:
  803      parser = argparse.ArgumentParser()
  804      parser.add_argument('--freeze-new', action='store_true',
  805                          help='observe and append planned cases that have no frozen row')
  806      parser.add_argument('--write-expected', action='store_true',
  807                          help='write vm-expected.json from the frozen observations (first freeze only)')
  808      args = parser.parse_args()
  809      BUILD.mkdir(parents=True, exist_ok=True)
  810      started = datetime.datetime.now(datetime.timezone.utc)
  811      built = oracles()
  812      if args.freeze_new:
  813          freeze(built)
  814          return 0
  815  
  816      reg = codec.registry()
  817      digest = codec.base_digest(reg)
  818      record = {'date': started.isoformat(), 'status': 'incomplete',
  819                'scope': 'knot-image-1 golden images and the frozen VM contract; no VM exists',
  820                'oracles': {lane: b['commit'] for lane, b in built.items()},
  821                'inputs': {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in
  822                           sorted([*HERE.glob('*.md'), *HERE.glob('*.py'), HERE / 'registry.json',
  823                                   *GOLDEN.glob('*'), *(HERE / 'oracles').glob('*'), *(HERE / 'bench').glob('*')])
  824                           if p.is_file()}}
  825      record['registry'] = check_registry(reg, built)
  826  
  827      frozen = json.loads((GOLDEN / 'expectations.json').read_text())
  828      cases = {c['name']: c for c in frozen['cases']}
  829      planned = [c['name'] for c in json.loads((GOLDEN / 'plan.json').read_text())['cases']]
  830      require(sorted(planned) == sorted(cases) and len(planned) == len(cases), 'plan.json and expectations.json list the same cases')
  831      for c in cases.values():
  832          require(sha((ROOT / c['source']).read_bytes()) == c['sha256'], f"frozen source {c['name']}")
  833  
  834      with ThreadPoolExecutor(max_workers=4) as pool:
  835          fresh = dict(zip(cases, pool.map(lambda c: lanes(c, built), cases.values())))
  836  
  837      def display(case):
  838          tool = built[case['lane']]['check']
  839          return run([tool, *lane_prefix(case), case['source']], 120)
  840  
  841      with ThreadPoolExecutor(max_workers=4) as pool:
  842          displays = dict(zip(cases, pool.map(display, cases.values())))
  843  
  844      bounds = json.loads((GOLDEN / 'bounds.json').read_text())['cases']
  845      plans, images, fixtures, table = {}, {}, [], {}
  846      for name, case in cases.items():
  847          require(fresh[name]['seed'] == case['seed'], (name, 'seed drift', fresh[name]['seed'], case['seed']))
  848          require(fresh[name]['eval'] == case['eval'], (name, 'eval drift', fresh[name]['eval'], case['eval']))
  849          plan = json.loads((GOLDEN / f'{name}.plan.json').read_text())
  850          data = (GOLDEN / f'{name}.kimg').read_bytes()
  851          require(codec.encode(plan, digest) == data, f'{name}: committed image differs from its plan')
  852          require(codec.decode(data, digest) == plan, f'{name}: image does not decode to its plan')
  853          problems = codec.validate(plan, reg)
  854          require(not problems, (name, problems))
  855          check_declarations(plan, (ROOT / case['source']).read_text())
  856          shown = displays[name]
  857          if shown['exit'] == 0:
  858              derived = from_display(shown['stdout'], plan, (ROOT / case['source']).read_text(), reg)
  859              require(derived == plan['functions'], (name, 'plan differs from the checked core', derived))
  860              view = 'checked-core'
  861          else:
  862              require(plan['entry'] == 'program', f'{name}: no checked core for a Book plan')
  863              view = f"unavailable: {shown['stderr'].strip()}"
  864          table[name] = vm_expectation(case, plan, bounds)
  865          plans[name], images[name] = plan, data
  866          fixtures.append({'name': name, 'lane': case['lane'], 'seed_lane': case.get('seed_lane', 'bun'),
  867                           'features': case['features'], 'image_sha256': sha(data), 'words': len(data) // 4,
  868                           'plan_matches': view, 'seed': classify(case['seed']), 'eval': classify(case['eval']),
  869                           'vm': table[name]})
  870  
  871      expected = {'rule': 'SPEC section 9: the VM owes the seed value wherever the seed succeeds within the '
  872                          'declared domain and budgets; eval-cli supplies the describe text where it agrees.',
  873                  'fuel': VM_FUEL, 'bounds': bounds, 'cases': table}
  874      if args.write_expected:
  875          EXPECTED.write_text(json.dumps(expected, indent=1) + '\n')
  876      require(json.loads(EXPECTED.read_text()) == expected, 'vm-expected.json differs from the rule')
  877  
  878      opcodes = {n[0] for p in plans.values() for n in walk(p)}
  879      require(opcodes == set(codec.OPCODES), f'uncovered node forms {set(codec.OPCODES) - opcodes}')
  880      modes = {n[4] for p in plans.values() for n in walk(p) if n[0] == 'case'}
  881      require(modes == set(codec.CASE_MODES), 'both case modes')
  882      big = [n for p in plans.values() for n in walk(p) if n[0] == 'lit' and n[2] != 'String' and n[3] >= 1 << 31]
  883      require(big, 'a boxed scalar constant')
  884  
  885      controls = byte_controls(images, digest) + [
  886          (f'plan:{k}', codec.encode(p, digest), 'HostFailure image: validator: ', m) for k, p, m in plan_controls(plans)]
  887      boundaries = []
  888      for label, data, reason, message in controls:
  889          got = rejected(data, reg, digest)
  890          require(got is not None and got.startswith(reason) and message in got, f'control {label}: {got}')
  891          boundaries.append({'control': label, 'refused': got})
  892  
  893      mutants = codec_mutants(plans, images, controls, reg, digest) + source_mutants(cases, built)
  894      survivors = [m['mutant'] for m in mutants if not m['killed']]
  895      require(not survivors, f'surviving mutants {survivors}')
  896  
  897      record['bench'] = check_bench(built, reg)
  898      record.update(status='passed', fixtures=fixtures, boundaries=boundaries, mutants=mutants,
  899                    coverage={'opcodes': sorted(opcodes), 'case_modes': sorted(modes),
  900                              'program_images': sum(p['entry'] == 'program' for p in plans.values())})
  901      RECEIPT.parent.mkdir(parents=True, exist_ok=True)
  902      RECEIPT.write_text(json.dumps(record, indent=1) + '\n')
  903      print(f"vm-spec passed: {len(fixtures)} golden images, {len(boundaries)} refused controls, "
  904            f"{len(mutants)} killed mutants; {RECEIPT.relative_to(ROOT)}")
  905      return 0
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

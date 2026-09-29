<!-- prechecks packet v1; rule=expectation-independent; increment=vm-spec; head=e14d8581dc12; base=454bf3059679; builder=scripts/prechecks/packets@3a2ef420dff1; sources: vm/check-spec.py@e14d8581 sha256=3e4e0060d26798c3804c524a113b6f5ce99991c0ba932f24902e03465c9c2db4 -->
# Claim
Statements about where expected values come from:

- docs/compiler-campaign/GATES.md: It builds the pinned literals and closures heads' `eval-cli` and `check-cli` from `vm/oracles/` with the seed's native lane, re-executes the seed and eval-cli on 78 golden sources, and requires the frozen observations byte for byte.
- docs/compiler-campaign/GATES.md: It checks each committed image against its hand-written plan, the reference codec and an independent reading of Knot's checked core display.
- docs/compiler-campaign/GATES.md: It also checks the frozen VM expectation table, 61 refused malformed-image controls, five expectation and bench controls, 30 codec mutants and 3 source mutants, and the bench freeze: sources, guards, outputs and the seed-native measurements pinned by digest in `vm/bench/workloads.json`.
- vm/DECISIONS.md: An image may already encode the foreign id; that is not IO conformance. - **D18 (literals' machine).** `knot-literals-wasm-1` and its emitters stay frozen in S as a native profile whose modules must stay byte-identical inside the VM. knot-vm-1 is a separate runtime for knot-image-1, with uniform RC and immortal constants from the start; it is not a growth of that machine.

# Evidence
`vm/check-spec.py:507-543` function `vm_expectation`, which builds expected values:
```python
  507  def vm_expectation(case, plan, bounds, source) -> dict:
  508      """The Exhausted-lane rule, applied to the frozen observations of one golden."""
  509      seed, ev = case['seed'], case['eval']
  510      fuel = VM_FUEL
  511      if plan['entry'] == 'program':
  512          require(seed['exit'] == 0, 'program seed must succeed')
  513          return {'argv': ['IMAGE', str(fuel), '--'], 'exit': 0, 'stdout': seed['stdout'], 'stderr': '',
  514                  'basis': 'seed', 'eval_lane': classify(ev)}
  515      if case['name'] in bounds:
  516          bound = bounds[case['name']]
  517          row = {'argv': ['IMAGE', 'main', str(fuel)], 'outcome': bound.get('outcome', 'Exhausted')}
  518          if row['outcome'] == 'Exhausted':
  519              row['kind'] = bound['kind']
  520          else:
  521              # Section 11's Book-describe bound: a scalar result has no describe spelling.
  522              require(bound['cause'] == 'invoke scalar-result', f"{case['name']}: unknown bound {bound['cause']}")
  523              main, rep = next(f for f in plan['functions'] if f['name'] == 'main'), plan.get('representation', {})
  524              require(main['result'] in [rep.get(r) for r in ('U32', 'Char', 'String') if r in rep],
  525                      f"{case['name']}: a scalar-result bound needs a scalar main")
  526          require(seed['exit'] == 0, f"{case['name']}: a bound excuses only a succeeding seed")
  527          return {**row, 'cause': bound['cause'], 'basis': 'bound', 'reason': bound['basis'], 'eval_lane': classify(ev)}
  528      require(seed['exit'] == 0, f"{case['name']}: the seed must succeed")
  529      value = described(seed['stdout'], erased_fields(source))
  530      if ev['exit'] == 0:
  531          _, _, tree = result_view(plan, ev['stdout'])
  532          require(tree == value, f"{case['name']}: eval-cli prints {tree!r}, the seed {value!r}")
  533          return {'argv': ['IMAGE', 'main', str(fuel)], 'exit': 0, 'stdout': ev['stdout'], 'stderr': '',
  534                  'basis': 'eval-cli', 'eval_lane': 'agree'}
  535      # The eval lane is excused only by a documented bound; the VM owes the seed's value.
  536      require(classify(ev) == 'Exhausted', f"{case['name']}: eval lane {ev} is not a documented bound")
  537      main = next(f for f in plan['functions'] if f['name'] == 'main')
  538      root = re.match(r'[\w.]+', value)[0]
  539      ctors = [c['name'] for c in plan['types'][main['result']]['constructors']]
  540      require(root in ctors, f"{case['name']}: seed root {root} is not a constructor of main's result")
  541      return {'argv': ['IMAGE', 'main', str(fuel)], 'exit': 0,
  542              'stdout': f"Evaluated\t{main['result']}\t{ctors.index(root)}\t{value}\n", 'stderr': '',
  543              'basis': 'seed', 'eval_lane': 'Exhausted'}
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

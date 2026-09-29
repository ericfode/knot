<!-- prechecks packet v1; rule=expectation-independent; increment=vm-spec; head=d2fe0f2048fb; base=454bf3059679; builder=scripts/prechecks/packets@47dbd98ca1c7; sources: vm/check-spec.py@d2fe0f20 sha256=a24f2a01dc7b977efbdc2e4c76336dc96fa8a07f1f620bbf34db2a2811ba0de1 -->
# Claim
Statements about where expected values come from:

- docs/compiler-campaign/GATES.md: It builds the pinned literals and closures heads' `eval-cli` and `check-cli` from `vm/oracles/` with the seed's native lane, re-executes the seed and eval-cli on 55 golden sources, and requires the frozen observations byte for byte.
- docs/compiler-campaign/GATES.md: It checks each committed image against its hand-written plan, the reference codec and an independent reading of Knot's checked core display.
- docs/compiler-campaign/GATES.md: It also checks the frozen VM expectation table, 48 refused malformed-image controls, 21 codec mutants and 3 source mutants, and the bench freeze.
- vm/DECISIONS.md: An image may already encode the foreign id; that is not IO conformance. - **D18 (literals' machine).** `knot-literals-wasm-1` and its emitters stay frozen in S as a native profile whose modules must stay byte-identical inside the VM. knot-vm-1 is a separate runtime for knot-image-1, with uniform RC and immortal constants from the start; it is not a growth of that machine.

# Evidence
`vm/check-spec.py:461-487` function `vm_expectation`, which builds expected values:
```python
  461  def vm_expectation(case, plan, bounds) -> dict:
  462      """The Exhausted-lane rule, applied to the frozen observations of one golden."""
  463      seed, ev = case['seed'], case['eval']
  464      fuel = VM_FUEL
  465      if plan['entry'] == 'program':
  466          require(seed['exit'] == 0, 'program seed must succeed')
  467          return {'argv': ['IMAGE', str(fuel), '--'], 'exit': 0, 'stdout': seed['stdout'], 'stderr': '',
  468                  'basis': 'seed', 'eval_lane': classify(ev)}
  469      if case['name'] in bounds:
  470          bound = bounds[case['name']]
  471          return {'argv': ['IMAGE', 'main', str(fuel)], 'outcome': 'Exhausted', 'kind': bound['kind'],
  472                  'cause': bound['cause'], 'basis': 'bound', 'reason': bound['basis'], 'eval_lane': classify(ev)}
  473      require(seed['exit'] == 0, f"{case['name']}: the seed must succeed")
  474      if ev['exit'] == 0:
  475          result_view(plan, ev['stdout'])
  476          return {'argv': ['IMAGE', 'main', str(fuel)], 'exit': 0, 'stdout': ev['stdout'], 'stderr': '',
  477                  'basis': 'eval-cli', 'eval_lane': 'agree'}
  478      # The eval lane is excused only by a documented bound; the VM owes the seed's value.
  479      require(classify(ev) == 'Exhausted', f"{case['name']}: eval lane {ev} is not a documented bound")
  480      main = next(f for f in plan['functions'] if f['name'] == 'main')
  481      m = re.fullmatch(r'(\w+)\{\}\n', seed['stdout'])
  482      require(m, f"{case['name']}: only a nullary seed value can be rendered without eval-cli")
  483      ctors = [c['name'] for c in plan['types'][main['result']]['constructors']]
  484      tag = ctors.index(m[1])
  485      return {'argv': ['IMAGE', 'main', str(fuel)], 'exit': 0,
  486              'stdout': f"Evaluated\t{main['result']}\t{tag}\t{m[1]}{{}}\n", 'stderr': '',
  487              'basis': 'seed', 'eval_lane': 'Exhausted'}
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

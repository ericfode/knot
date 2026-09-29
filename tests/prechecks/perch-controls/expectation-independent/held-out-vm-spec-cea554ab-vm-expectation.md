<!-- prechecks packet v1; rule=expectation-independent; increment=vm-spec; head=cea554abc93f; base=90b4052c1784; builder=scripts/prechecks/packets@3a2ef420dff1; sources: vm/check-spec.py@cea554ab sha256=9eb0d4ae01df310d01c91b7b88410c18f149a22d6de2692d036ec5dee87d2e7c -->
# Claim
Statements about where expected values come from:

- docs/COMPILER-CAMPAIGN.md: | | D7 | Every new capability gets fixed expectations from the pinned reference (seed) or literal review before implementation, and existing assertions stay unchanged.
- docs/COMPILER-CAMPAIGN.md: | | D10 | Data lifetime for milestone 1: unique `Type` objects plus reference-counted immutable `Data` (candidate B of `research/data-lifetime/`).
- docs/COMPILER-CAMPAIGN.md: | | D16 | VM fuel counts calls and invokes, independent of eval.bend's transition count.
- docs/COMPILER-CAMPAIGN.md: It stays in the bundle as a frozen native profile, and its opcode DSL seeds the later `vm-emit` speed track.

# Evidence
`vm/check-spec.py:690-727` function `vm_expectation`, which builds expected values:
```python
  690  def vm_expectation(case, plan, bounds, source, evaluator=None) -> dict:
  691      """The Exhausted-lane rule, applied to the frozen observations of one golden."""
  692      seed, ev = case['seed'], case['eval']
  693      fuel = VM_FUEL
  694      require('divergence' not in case or plan['entry'] == 'program', f"{case['name']}: only a Program's output diverges")
  695      if plan['entry'] == 'program':
  696          return output_expectation(case, plan, evaluator)
  697      main = next(f for f in plan['functions'] if f['name'] == 'main')
  698      why = codec.undescribable(plan, main['result'])
  699      if why:
  700          # Section 8: Knot has no describe spelling for this result type. D4's Unsupported,
  701          # derived from the image before any entry; not a bound and not agreement.
  702          require(case['name'] not in bounds, f"{case['name']}: a bound cannot stand in for Unsupported")
  703          return {'argv': ['IMAGE', 'main', str(fuel)], 'outcome': 'Unsupported', 'cause': 'invoke result-type',
  704                  'basis': 'describe-domain', 'reason': f'section 8: {why}', 'eval_lane': classify(ev)}
  705      if case['name'] in bounds:
  706          # Section 11: a bound is a declared domain or budget limit, and its outcome is Exhausted.
  707          bound = bounds[case['name']]
  708          require(sorted(bound) == ['basis', 'cause', 'kind'] and bound['kind'] in (1, 2, 3),
  709                  f"{case['name']}: a bound is Exhausted with a kind, a cause and a basis")
  710          require(seed['exit'] == 0, f"{case['name']}: a bound excuses only a succeeding seed")
  711          return {'argv': ['IMAGE', 'main', str(fuel)], 'outcome': 'Exhausted', 'kind': bound['kind'],
  712                  'cause': bound['cause'], 'basis': 'bound', 'reason': bound['basis'], 'eval_lane': classify(ev)}
  713      require(seed['exit'] == 0, f"{case['name']}: the seed must succeed")
  714      value = described(seed['stdout'], erased_fields(source))
  715      if ev['exit'] == 0:
  716          _, _, tree = result_view(plan, ev['stdout'])
  717          require(tree == value, f"{case['name']}: eval-cli prints {tree!r}, the seed {value!r}")
  718          return {'argv': ['IMAGE', 'main', str(fuel)], 'exit': 0, 'stdout': ev['stdout'], 'stderr': '',
  719                  'basis': 'eval-cli', 'eval_lane': 'agree'}
  720      # The eval lane is excused only by a documented bound; the VM owes the seed's value.
  721      excuse = eval_excuse(case, plan, value, evaluator)
  722      root = re.match(r'[\w.]+', value)[0]
  723      ctors = [c['name'] for c in plan['types'][main['result']]['constructors']]
  724      require(root in ctors, f"{case['name']}: seed root {root} is not a constructor of main's result")
  725      return {'argv': ['IMAGE', 'main', str(fuel)], 'exit': 0,
  726              'stdout': f"Evaluated\t{main['result']}\t{ctors.index(root)}\t{value}\n", 'stderr': '',
  727              'basis': 'seed', 'eval_lane': 'Exhausted', 'eval_bound': excuse}
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

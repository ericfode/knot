<!-- prechecks packet v1; rule=claim-holds-against-evidence; increment=vm-spec; head=e14d8581dc12; base=454bf3059679; builder=scripts/prechecks/packets@3a2ef420dff1; sources: vm/SPEC.md@e14d8581 sha256=775b305468384b9e8ec07490db7b51716e2d159635be1d9b3e3ab584923842ac; vm/check-spec.py@e14d8581 sha256=3e4e0060d26798c3804c524a113b6f5ce99991c0ba932f24902e03465c9c2db4 -->
# Claim
vm/SPEC.md:585-587 (section: 11. Outcomes and the Exhausted-lane rule) - verbatim text:

> A lane may be excused **only** by a
> documented bound, and its receipt must name the bound, the budget and the boundary
> reached:

# Evidence
Evidence: the changed regions that share the most words with the claim (diff hunks of modified files, declarations of added files).
```
`vm/check-spec.py:34-34` (added)
   34  EVAL_BUDGET = '1048576'

`vm/check-spec.py:35-35` (added)
   35  DISPLAY_VISITS = 1_048_576  # SPEC section 8's rendering bound

`vm/check-spec.py:37-37` (added)
   37  RECEIPT = HERE / 'receipts/spec.json'

`vm/check-spec.py:112-113` (added)
  112  def eval_argv(case, built):
  113      return [built[case['lane']]['eval'], *lane_prefix(case), case['source'], 'main', EVAL_BUDGET]

`vm/check-spec.py:475-504` (added)
  475  def described(printed: str, quantities: dict) -> str:
  476      """The seed's printed value in SPEC section 8's describe spelling: no spaces, erased
  477      fields dropped by the golden's own declarations, a Nat as its unary view."""
  478      s, at = printed.removesuffix('\n'), 0
  479      token = re.compile(r'(\d+)n|([\w.]+)\{')
  480  
  481      def value():
  482          nonlocal at
  483          m = token.match(s, at)
  484          require(m, f'seed value: cannot read {s[at:at + 30]!r}')
  485          at = m.end()
  486          if m[1] is not None:
  487              n = int(m[1])
  488              require(n <= DISPLAY_VISITS, f'seed value: Nat {n} exceeds the display bound')
  489              return 'Succ{' * n + 'Zero{}' + '}' * n
  490          kids = []
  491          while not s.startswith('}', at):
  492              kids.append(value())
  493              if s.startswith(', ', at):
  494                  at += 2
  495              else:
  496                  require(s.startswith('}', at), f'seed value: cannot read {s[at:at + 30]!r}')
  497          at += 1
  498          live = quantities.get(m[2], [1] * len(kids))
  499          require(len(live) == len(kids), f'seed value: {m[2]} has {len(kids)} fields, declared {len(live)}')
  500          return m[2] + '{' + ','.join(k for q, k in zip(live, kids) if q) + '}'
  501  
  502      tree = value()
  503      require(at == len(s), f'seed value: trailing text {s[at:at + 30]!r}')
  504      return tree

`vm/check-spec.py:507-543` (added)
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

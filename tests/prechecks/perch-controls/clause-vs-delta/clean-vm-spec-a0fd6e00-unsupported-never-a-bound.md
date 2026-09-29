<!-- prechecks packet v1; rule=clause-vs-delta; increment=vm-spec; head=a0fd6e00c706; base=481bb3188010; builder=scripts/prechecks/packets@3a2ef420dff1; sources: vm/SPEC.md@a0fd6e00 sha256=d0666796ac67a26f36f9c01137822d14ab7ae847ed1462dc92d35b5b7a31ad11; vm/check-spec.py@a0fd6e00 sha256=2cad8c30f3ac305c3c5301619e765f60fc6e955850cd8c4724f8c62248cfaca4 -->
# Claim
Invariance clause (vm/SPEC.md):

> An Unsupported outcome is D4's refusal of a form Knot does not handle: a recorded capability gap, never a bound.

# Evidence
Evidence: the governed diff hunks (base to head).
```
`vm/check-spec.py:37-37` (added)
   37  DISPLAY_VISITS = 1_048_576  # SPEC section 8's rendering bound

`vm/check-spec.py:70-78` (added)
   70  def run(argv, timeout):
   71      argv = [str(x) for x in argv]
   72      try:
   73          p = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=timeout * SCALE,
   74                             env={**os.environ, 'BEND_NO_TELEMETRY': '1'})
   75      except subprocess.TimeoutExpired:
   76          return {'exit': None, 'outcome': 'harness-timeout', 'stdout': '', 'stderr': ''}
   77      return {'exit': p.returncode, 'stdout': p.stdout.decode('utf-8', 'replace'),
   78              'stderr': p.stderr.decode('utf-8', 'replace'), 'bytes': p.stdout}

`vm/check-spec.py:649-686` (added)
  649  def vm_expectation(case, plan, bounds, source, evaluator=None) -> dict:
  650      """The Exhausted-lane rule, applied to the frozen observations of one golden."""
  651      seed, ev = case['seed'], case['eval']
  652      fuel = VM_FUEL
  653      require('divergence' not in case or plan['entry'] == 'program', f"{case['name']}: only a Program's output diverges")
  654      if plan['entry'] == 'program':
  655          return output_expectation(case, plan, evaluator)
  656      main = next(f for f in plan['functions'] if f['name'] == 'main')
  657      why = codec.undescribable(plan, main['result'])
  658      if why:
  659          # Section 8: Knot has no describe spelling for this result type. D4's Unsupported,
  660          # derived from the image before any entry; not a bound and not agreement.
  661          require(case['name'] not in bounds, f"{case['name']}: a bound cannot stand in for Unsupported")
  662          return {'argv': ['IMAGE', 'main', str(fuel)], 'outcome': 'Unsupported', 'cause': 'invoke result-type',
  663                  'basis': 'describe-domain', 'reason': f'section 8: {why}', 'eval_lane': classify(ev)}
  664      if case['name'] in bounds:
  665          # Section 11: a bound is a declared domain or budget limit, and its outcome is Exhausted.
  666          bound = bounds[case['name']]
  667          require(sorted(bound) == ['basis', 'cause', 'kind'] and bound['kind'] in (1, 2, 3),
  668                  f"{case['name']}: a bound is Exhausted with a kind, a cause and a basis")
  669          require(seed['exit'] == 0, f"{case['name']}: a bound excuses only a succeeding seed")
  670          return {'argv': ['IMAGE', 'main', str(fuel)], 'outcome': 'Exhausted', 'kind': bound['kind'],
  671                  'cause': bound['cause'], 'basis': 'bound', 'reason': bound['basis'], 'eval_lane': classify(ev)}
  672      require(seed['exit'] == 0, f"{case['name']}: the seed must succeed")
  673      value = described(seed['stdout'], erased_fields(source))
  674      if ev['exit'] == 0:
  675          _, _, tree = result_view(plan, ev['stdout'])
  676          require(tree == value, f"{case['name']}: eval-cli prints {tree!r}, the seed {value!r}")
  677          return {'argv': ['IMAGE', 'main', str(fuel)], 'exit': 0, 'stdout': ev['stdout'], 'stderr': '',
  678                  'basis': 'eval-cli', 'eval_lane': 'agree'}
  679      # The eval lane is excused only by a documented bound; the VM owes the seed's value.
  680      require(classify(ev) == 'Exhausted', f"{case['name']}: eval lane {ev} is not a documented bound")
  681      root = re.match(r'[\w.]+', value)[0]
  682      ctors = [c['name'] for c in plan['types'][main['result']]['constructors']]
  683      require(root in ctors, f"{case['name']}: seed root {root} is not a constructor of main's result")
  684      return {'argv': ['IMAGE', 'main', str(fuel)], 'exit': 0,
  685              'stdout': f"Evaluated\t{main['result']}\t{ctors.index(root)}\t{value}\n", 'stderr': '',
  686              'basis': 'seed', 'eval_lane': 'Exhausted'}

`vm/check-spec.py:707-744` (added)
  707  def invocation_expectations(case, plan, source, evaluator=None) -> list:
  708      """Section 8 for each frozen Book invocation: the image-derived verdict, or the entered
  709      function's describe line from the reference evaluation. eval-cli is the oracle; a row
  710      that differs from it declares the image loss that explains the difference."""
  711      ev, rows = evaluator or reference, []
  712      for i in case.get('invocations', []):
  713          name, ordinals = i['argv'][0], [int(o) for o in i['argv'][1:]]
  714          label, observed_eval = f"{case['name']} {' '.join(i['argv'])}", i['eval']
  715          row = {'argv': ['IMAGE', name, str(VM_FUEL), *i['argv'][1:]]}
  716          verdict = codec.invocation(plan, name, ordinals)
  717          if verdict:
  718              outcome, cause = verdict.split(' ', 1)
  719              row.update(outcome=outcome, cause=cause)
  720              review = verdict
  721              agrees = observed_eval['exit'] == 5 and observed_eval['stderr'] == verdict.replace(' ', '\t') + '\n'
  722          else:
  723              got = ev.book(plan, name, ordinals, VM_FUEL)
  724              require(got.get('exit') == 0, f'{label}: the reference evaluation gives {got}')
  725              row.update(exit=0, stdout=got['stdout'], stderr='')
  726              review = got['stdout'].split('\t')[3].removesuffix('\n')
  727              agrees = observed_eval['exit'] == 0 and observed_eval['stdout'] == got['stdout']
  728          require(i['vm'] == review, f"{label}: literal review {i['vm']!r}, section 8 gives {review!r}")
  729          if verdict == 'Unsupported invoke result-type':
  730              # eval-cli enters it and reports InternalFailure eval result-tag (DECISIONS finding 7).
  731              require('divergence' not in i, f'{label}: an Unsupported result is D4\'s refusal, not a divergence')
  732              row['basis'] = 'describe-domain'
  733          elif agrees:
  734              require('divergence' not in i, f'{label}: declared {i.get("divergence")!r}, but eval-cli agrees')
  735              row['basis'] = 'eval-cli'
  736          else:
  737              loss = image_loss(plan, name, ordinals, source)
  738              require(loss is not None and i.get('divergence') == loss,
  739                      f'{label}: eval-cli gives {observed_eval}, section 8 {review!r}; declared {i.get("divergence")!r}, '
  740                      f'image loss {loss!r}')
  741              row['basis'] = f'divergent-by-contract ({loss})'
  742          row['eval_lane'] = classify(observed_eval)
  743          rows.append(row)
  744      return rows

`vm/check-spec.py:770-826` (added)
  770  def expectation_controls(cases: dict, plans: dict, bounds: dict, sources: dict, evaluator=None) -> list:
  771      """What the rule must refuse: an eval lane that disagrees with the seed, a bound that is
  772      not Exhausted or that stands in for an Unsupported result, and a D20 classification that
  773      is not the program's own output."""
  774      def row(label, seed, ev):
  775          return {'name': f'control:{label}', 'seed': {'exit': 0, 'stdout': seed, 'stderr': ''},
  776                  'eval': {'exit': 0, 'stdout': ev, 'stderr': ''}}
  777  
  778      def without(name, *keys):
  779          return {k: v for k, v in cases[name].items() if k not in keys}
  780  
  781      def emoji(plan):
  782          """print-non-scalar-wide's plan printing U+1F600, which its native bytes cannot tell apart."""
  783          plan = json.loads(json.dumps(plan))
  784          plan['functions'][1]['body'][3][0][3][0][3][0][3] = 0x1F600
  785          return plan
  786      describe_bound = {'outcome': 'HostFailure', 'cause': 'invoke scalar-result',
  787                        'basis': 'round 1: a Book-describe bound, which section 11 no longer admits'}
  788      unprinted, second = cases['non-scalar-unprinted'], cases['print-non-scalar-second']
  789      out = []
  790      for label, name, case, table, plan in [
  791              ('eval-disagrees', 'value-on', row('eval-disagrees', 'Off{}\n', 'Evaluated\t0\t1\tOn{}\n'), bounds, None),
  792              ('eval-keeps-erased-field', 'erased-construct',
  793               row('eval-keeps-erased-field', 'ProofBox{Off{}, On{}}\n', 'Evaluated\t1\t0\tProofBox{Off{}}\n'), bounds, None),
  794              ('eval-nat-binds-n', 'nat-pred',
  795               row('eval-nat-binds-n', '2n\n', 'Evaluated\t0\t1\tSucc{Succ{Succ{Zero{}}}}\n'), bounds, None),
  796              ('bound-not-exhausted', 'value-on', cases['value-on'], {**bounds, 'value-on': describe_bound}, None),
  797              ('bound-for-unsupported', 'result-u32', cases['result-u32'], {**bounds, 'result-u32': describe_bound}, None),
  798              # D20: a declared divergence exactly where the program prints a non-scalar Char.
  799              ('non-scalar-as-agreement', 'print-non-scalar', without('print-non-scalar', 'divergence', 'vm_stdout'), bounds, None),
  800              ('divergence-on-scalar-output', 'foreign-print',
  801               {**cases['foreign-print'], 'divergence': NON_SCALAR, 'vm_stdout': ''}, bounds, None),
  802              ('divergence-other-class', 'print-non-scalar', {**cases['print-non-scalar'], 'divergence': 'other'}, bounds, None),
  803              ('vm-writes-non-scalar', 'print-non-scalar-mid',
  804               {**cases['print-non-scalar-mid'], 'vm_stdout': cases['print-non-scalar-mid']['seed']['stdout']}, bounds, None),
  805              ('wide-code-as-agreement', 'print-non-scalar-wide',
  806               without('print-non-scalar-wide', 'divergence', 'vm_stdout'), bounds, None),
  807              # The native bytes of Chr{67237376} are those of U+1F600; the plan's value decides.
  808              ('wide-plan-as-u1f600', 'print-non-scalar-wide', cases['print-non-scalar-wide'], bounds,
  809               emoji(plans['print-non-scalar-wide'])),
  810              # The Bun lane refuses a non-scalar Char where it is built, printed or not.
  811              ('unprinted-as-divergence', 'non-scalar-unprinted',
  812               {**unprinted, 'divergence': NON_SCALAR, 'vm_stdout': 'a\n'}, bounds, None),
  813              ('second-output-from-bun', 'print-non-scalar-second', {**second, 'vm_stdout': second['seed_bun']['stdout']},
  814               bounds, None),
  815              ('native-other-bytes', 'print-non-scalar',
  816               {**cases['print-non-scalar'], 'seed': {**cases['print-non-scalar']['seed'], 'stdout_hex': 'efbfbd0a'}}, bounds, None),
  817              ('bun-beyond-vm', 'non-scalar-unprinted',
  818               {**unprinted, 'seed_bun': {**unprinted['seed_bun'], 'stdout': 'b\n'}}, bounds, None),
  819              ('native-without-bun-record', 'print-non-scalar-wide', without('print-non-scalar-wide', 'seed_bun'), bounds, None)]:
  820          try:
  821              vm_expectation(case, plan or plans[name], table, sources[name], evaluator)
  822          except AssertionError as refusal:
  823              out.append({'control': f'expectation:{label}', 'refused': str(refusal)})
  824              continue
  825          raise AssertionError(f'expectation control {label} was admitted')
  826      return out

`vm/check-spec.py:829-831` (added)
  829  def classify(result) -> str:
  830      return {0: 'agree', 2: 'Invalid', 3: 'Unsupported', 4: 'Exhausted', 5: 'HostFailure',
  831              6: 'InternalFailure'}.get(result['exit'], 'other')

`vm/check-spec.py:834-842` (added)
  834  def reproduced(name: str, plan: dict, expected: dict, evaluator=None):
  835      """The reference evaluation reproduces a Book golden's expectation: its describe line, or
  836      its bound's Exhausted outcome. A result section 8 cannot describe is never entered."""
  837      if plan['entry'] != 'book' or expected.get('outcome') == 'Unsupported':
  838          return
  839      got = (evaluator or reference).book(plan, 'main', [], VM_FUEL)
  840      keys = ('exit', 'stdout') if 'exit' in expected else ('outcome', 'kind', 'cause')
  841      require({k: got.get(k) for k in keys} == {k: expected.get(k) for k in keys},
  842              f'{name}: the reference evaluation gives {got}')

`vm/check-spec.py:1074-1074` (added)
 1074  ILL_TYPED = {'outcome': 'HostFailure', 'cause': 'image ill-typed'}
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

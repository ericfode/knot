<!-- prechecks packet v1; rule=kill-is-semantic; increment=vm-spec; head=63e63203bb2e; base=454bf3059679; builder=manual-excerpt@3a2ef420dff1; sources: docs/COMPILER-CAMPAIGN.md@63e63203 sha256=223cf76f13cd0911819691eacd2d5de09dc4b8e62d296675c6c6a9e3beb5b294; docs/compiler-campaign/GATES.md@63e63203 sha256=5afd556faeac28d0296931159c7b6e76dce24de9bb18986e9c92184992819f34; vm/check-spec.py@63e63203 sha256=016a7b2a0bef5180a5818283874301c693b056bfd9e03d98cb614e1d0a13f511; vm/check-spec.py@63e63203 sha256=016a7b2a0bef5180a5818283874301c693b056bfd9e03d98cb614e1d0a13f511; vm/check-spec.py@63e63203 sha256=016a7b2a0bef5180a5818283874301c693b056bfd9e03d98cb614e1d0a13f511; vm/check-spec.py@63e63203 sha256=016a7b2a0bef5180a5818283874301c693b056bfd9e03d98cb614e1d0a13f511 -->
# Claim
`docs/compiler-campaign/GATES.md:80-88` (vm-spec gate: source mutants)

> whose review declares the line. It also checks the frozen VM expectation table; 71 refused image controls,
> nine of them on either side of the resource limits that are `Exhausted` kind 2; 27
> expectation, seven invocation, two seed-display, three display-lane and two bench
> controls; two excused eval-bound controls; six admitted plan controls, one admitted
> limit control, seven admitted code-list controls and 60 run controls with their frozen
> fuel, calls and outcomes (among them the D22 refusal of an effect under a Book entry
> and D20 on a Halt's message); nine describe-domain controls; 13 argument controls;
> the lowering of two hand-written displays; 70 codec, 4 source, 57 evaluator and ten
> rule mutants of `check-spec.py` itself; and the bench freeze: sources, guards, outputs and the seed-native

`docs/COMPILER-CAMPAIGN.md:41-43` (trusted-runtime definition of done)

>      - VM ⇔ model after every transition on small images;
>      - VM ⇔ `src/eval.bend` ⇔ seed on the values of every frozen suite, where Exhausted excuses a lane only under a documented bound;
>      - mutants killed by named gates.

# Evidence
`vm/check-spec.py:71-90` (run and observed)

```
   71  def run(argv, timeout):
   72      argv = [str(x) for x in argv]
   73      try:
   74          p = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=timeout * SCALE,
   75                             env={**os.environ, 'BEND_NO_TELEMETRY': '1'})
   76      except subprocess.TimeoutExpired:
   77          return {'exit': None, 'outcome': 'harness-timeout', 'stdout': '', 'stderr': ''}
   78      return {'exit': p.returncode, 'stdout': p.stdout.decode('utf-8', 'replace'),
   79              'stderr': p.stderr.decode('utf-8', 'replace'), 'bytes': p.stdout}
   80  
   81  
   82  def observed(result):
   83      """Exit and text; a stdout that is not UTF-8 (the native lane's non-scalar output) is
   84      also kept exactly, as hex."""
   85      row = {k: result[k] for k in ('exit', 'stdout', 'stderr')}
   86      try:
   87          result.get('bytes', b'').decode('utf-8')
   88      except UnicodeDecodeError:
   89          row['stdout_hex'] = result['bytes'].hex()
   90      return row
```

`vm/check-spec.py:133-142` (seed_observation)

```
  133  def seed_observation(case, source=None):
  134      source = source or case['source']
  135      if case.get('seed_lane') == 'native':
  136          out = BUILD / 'native' / case['name']
  137          out.parent.mkdir(parents=True, exist_ok=True)
  138          built = run([SEED, source, '-o', out], 900)
  139          require(built['exit'] == 0, (case['name'], built))
  140          return run([out], 120)
  141      return run([SEED, source], 120)
  142  
```

`vm/check-spec.py:152-162` (lanes)

```
  152  def lanes(case, built):
  153      got = {'seed': observed(seed_observation(case)),
  154             'eval': observed(run(eval_argv(case, built), 120))}
  155      if 'seed_bun_stderr' in case:
  156          # The seed's Bun lane, recorded beside a native observation; it never classifies.
  157          got['seed_bun'] = observed(run([SEED, case['source']], 120))
  158      if 'invocations' in case:
  159          # The seed runs only `main`; eval-cli is the oracle for every other invocation.
  160          got['invocations'] = [{**reviewed(i), 'eval': observed(run(invoke_argv(case, built, i), 120))}
  161                                for i in case['invocations']]
  162      return got
```

`vm/check-spec.py:2298-2319` (SOURCE_MUTANTS and source_mutants)

```
 2298  SOURCE_MUTANTS = [
 2299      ('case-on', 'flip(On{})', 'flip(Off{})'),
 2300      ('u32-wrap', 'U32.add(4294967295,1)', 'U32.add(4294967295,2)'),
 2301      ('closure-capture-on', 'capture(On{})', 'capture(Off{})'),
 2302      ('string-surrogate-pair', '"\\u{1f600}"', '"\\u{d83d}\\u{de00}"'),
 2303  ]
 2304  
 2305  
 2306  def source_mutants(cases, built) -> list:
 2307      out = []
 2308      for name, old, new in SOURCE_MUTANTS:
 2309          case = cases[name]
 2310          text = (ROOT / case['source']).read_text()
 2311          require(text.count(old) == 1, f'source mutant {name}')
 2312          path = BUILD / 'mutants' / f'{name}.bend'
 2313          path.parent.mkdir(parents=True, exist_ok=True)
 2314          path.write_text(text.replace(old, new))
 2315          mutated = dict(case, source=path.relative_to(ROOT).as_posix())
 2316          got = lanes(mutated, built)
 2317          killed = got['seed'] != case['seed'] and got['eval'] != case['eval']
 2318          out.append({'mutant': f'source:{name}', 'killed': killed, 'seed': got['seed'], 'eval': got['eval']})
 2319      return out
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

<!-- prechecks packet v1; rule=kill-is-semantic; increment=vm-spec; head=cea554abc93f; base=none; builder=manual-excerpt@3a2ef420dff1; sources: vm/SPEC.md@cea554ab sha256=66a6a69b70833beafc31ae0e8924e7f9394ab62e39ca9aa4bb5d7a78446711b5; vm/check-spec.py@cea554ab sha256=9eb0d4ae01df310d01c91b7b88410c18f149a22d6de2692d036ec5dee87d2e7c; vm/check-spec.py@cea554ab sha256=9eb0d4ae01df310d01c91b7b88410c18f149a22d6de2692d036ec5dee87d2e7c; vm/check-spec.py@cea554ab sha256=9eb0d4ae01df310d01c91b7b88410c18f149a22d6de2692d036ec5dee87d2e7c; vm/check-spec.py@cea554ab sha256=9eb0d4ae01df310d01c91b7b88410c18f149a22d6de2692d036ec5dee87d2e7c; vm/check-spec.py@cea554ab sha256=9eb0d4ae01df310d01c91b7b88410c18f149a22d6de2692d036ec5dee87d2e7c -->
# Claim
`vm/SPEC.md:756-757` (section 11. Outcomes and the Exhausted-lane rule)

> result that §8 cannot describe; a broken invariant is a defect. A timeout or
> crash never counts as a semantic mutant kill.

# Evidence
`vm/check-spec.py:71-90` (run, observed)

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

`vm/check-spec.py:133-141` (seed_observation)

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

`vm/check-spec.py:2034-2039` (SOURCE_MUTANTS)

```
 2034  SOURCE_MUTANTS = [
 2035      ('case-on', 'flip(On{})', 'flip(Off{})'),
 2036      ('u32-wrap', 'U32.add(4294967295,1)', 'U32.add(4294967295,2)'),
 2037      ('closure-capture-on', 'capture(On{})', 'capture(Off{})'),
 2038      ('string-surrogate-pair', '"\\u{1f600}"', '"\\u{d83d}\\u{de00}"'),
 2039  ]
```

`vm/check-spec.py:2042-2055` (source_mutants)

```
 2042  def source_mutants(cases, built) -> list:
 2043      out = []
 2044      for name, old, new in SOURCE_MUTANTS:
 2045          case = cases[name]
 2046          text = (ROOT / case['source']).read_text()
 2047          require(text.count(old) == 1, f'source mutant {name}')
 2048          path = BUILD / 'mutants' / f'{name}.bend'
 2049          path.parent.mkdir(parents=True, exist_ok=True)
 2050          path.write_text(text.replace(old, new))
 2051          mutated = dict(case, source=path.relative_to(ROOT).as_posix())
 2052          got = lanes(mutated, built)
 2053          killed = got['seed'] != case['seed'] and got['eval'] != case['eval']
 2054          out.append({'mutant': f'source:{name}', 'killed': killed, 'seed': got['seed'], 'eval': got['eval']})
 2055      return out
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

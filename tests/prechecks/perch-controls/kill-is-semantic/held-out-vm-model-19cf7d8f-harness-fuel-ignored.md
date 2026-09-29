<!-- prechecks packet v1; rule=kill-is-semantic; increment=vm-model; head=19cf7d8f71ff; base=none; builder=manual-excerpt@3a2ef420dff1; sources: docs/compiler-campaign/GATES.md@19cf7d8f sha256=7362b12f5126a8f03d2c4a3c0e39731448da147efe0e56e6bf06ec7953638d95; vm/check-model.py@19cf7d8f sha256=f9d4dd03a9050086e0f05b793c504480690a6c8fe5fe27593f71f935d2901f77; vm/check-model.py@19cf7d8f sha256=f9d4dd03a9050086e0f05b793c504480690a6c8fe5fe27593f71f935d2901f77; vm/check-model.py@19cf7d8f sha256=f9d4dd03a9050086e0f05b793c504480690a6c8fe5fe27593f71f935d2901f77; vm/check-model.py@19cf7d8f sha256=f9d4dd03a9050086e0f05b793c504480690a6c8fe5fe27593f71f935d2901f77; vm/check-model.py@19cf7d8f sha256=f9d4dd03a9050086e0f05b793c504480690a6c8fe5fe27593f71f935d2901f77; vm/check-model.py@19cf7d8f sha256=f9d4dd03a9050086e0f05b793c504480690a6c8fe5fe27593f71f935d2901f77 -->
# Claim
`docs/compiler-campaign/GATES.md:99-100`

> printing `All terms check.`; and 24 model mutants killed by a wrong observation,
> never a crash, seven of them also refuted by a law of `vm/PROOF.bend`. It writes

# Evidence
`vm/check-model.py:101-109` (run)

```
  101  def run(argv, timeout, cwd=ROOT):
  102      argv = [str(x) for x in argv]
  103      try:
  104          p = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=timeout * SCALE,
  105                             env={**os.environ, 'BEND_NO_TELEMETRY': '1'})
  106      except subprocess.TimeoutExpired:
  107          return {'exit': None, 'stdout': '', 'stderr': 'harness-timeout'}
  108      return {'exit': p.returncode, 'stdout': p.stdout.decode('utf-8', 'replace'),
  109              'stderr': p.stderr.decode('utf-8', 'replace')}
```

`vm/check-model.py:255-260` (KNOWN_EXITS, well_formed)

```
  255  KNOWN_EXITS = {0, 3, 4, 5, 6, 7}
  256  
  257  
  258  def well_formed(result) -> bool:
  259      """A model answer, not a crash, trap or timeout: those never count as a kill."""
  260      return result['exit'] in KNOWN_EXITS and 'bend:' not in result['stderr']
```

`vm/check-model.py:276-287` (agrees)

```
  276  def agrees(case: dict, got: dict) -> bool:
  277      if 'outcome' not in case:
  278          return (got['exit'], got['stderr']) == (case['exit'], case.get('stderr', '')) and written(case, got)
  279      fields = got['stderr'].rstrip('\n').split('\t')
  280      if case['outcome'] == 'Exhausted':
  281          # A Program that runs out of fuel keeps what it wrote (SPEC section 7).
  282          return got['exit'] == 4 and written(case, got) and fields == ['Exhausted', 'vm', str(case['kind']), case['cause']]
  283      if case['outcome'] == 'Unsupported':
  284          return got['exit'] == 3 and got['stdout'] == '' and fields == ['Unsupported', *case['cause'].split(' ')]
  285      if case['outcome'] == 'HostFailure':
  286          return got['exit'] == 5 and written(case, got) and fields == ['HostFailure', *case['cause'].split(' ')]
  287      return False
```

`vm/check-model.py:474-494` (admitted_runs)

```
  474  def admitted_runs(model: Path, audit: Path, listed: list, argv=control_argv) -> dict:
  475      """Each admitted control's run at its fuel, its RC audit and its entries paid for."""
  476      folder = BUILD / 'admitted'
  477      folder.mkdir(parents=True, exist_ok=True)
  478  
  479      def one(item):
  480          label, plan, fuel, want, calls = item
  481          path = folder / (label.replace(':', '_') + '.kimg')
  482          data = codec.encode(plan, DIGEST)
  483          if not path.exists() or path.read_bytes() != data:
  484              path.write_bytes(data)
  485          result = run(argv(model, path, plan, fuel), 120)
  486          audited = run(argv(audit, path, plan, fuel), 300)
  487          m = AUDIT.match(audited['stdout'].strip())
  488          balanced = bool(m) and audited['exit'] == 0 and m.group(1) == 'passed' and (
  489              'exit' not in want or m.group(4) == '0') and int(m.group(5)) == calls
  490          # A kill is judged on the observation that went wrong.
  491          return label, {'result': audited if agrees(want, result) else result,
  492                         'agrees': agrees(want, result) and balanced, 'calls': int(m.group(5)) if m else None}
  493      with ThreadPoolExecutor(max_workers=8) as pool:
  494          return dict(pool.map(one, listed))
```

`vm/check-model.py:497-512` (fuel_ignored, harness_runs)

```
  497  # Harness mutants: the gate's own reading of the run controls, weakened. Each runs the
  498  # run controls against the base model and must be killed by the controls named.
  499  def fuel_ignored(binary: Path, path: Path, plan: dict, fuel: int) -> list:
  500      return control_argv(binary, path, plan, cs.VM_FUEL)
  501  
  502  
  503  def harness_runs(model: Path, audit: Path, admitted: list, base: dict) -> list:
  504      """`fuel-ignored` runs every control at 1,000,000: exactly the fuel controls whose frozen
  505      run differs from the reference evaluation's at 1,000,000 must kill it."""
  506      runs = [a for a in admitted if a[0].startswith('run:')]
  507      killers = sorted(label for label, plan, fuel, want, calls in runs
  508                       if fuel != cs.VM_FUEL and cs.ran(plan, {**want, 'calls': calls}) != {**want, 'calls': calls})
  509      got = admitted_runs(model, audit, runs, fuel_ignored)
  510      killed = sorted(n for n, r in got.items() if not r['agrees'] and base[n]['agrees'])
  511      require(killers and killed == killers, f'harness mutant fuel-ignored: killed by {killed}, the fuel controls {killers}')
  512      return [{'mutant': 'fuel-ignored', 'breaks': 'each run control runs at 1,000,000, not its frozen fuel', 'by': killed}]
```

`vm/check-model.py:927-935` (kills)

```
  927  def kills(base: dict, mutant: dict) -> list:
  928      """Checks whose observation changed to a well-formed wrong one."""
  929      killed = []
  930      for check, rows in mutant.items():
  931          for name, row in rows.items():
  932              if not row['agrees'] and base[check][name]['agrees'] and (
  933                      check == 'sweep' or well_formed(row['result'])):
  934                  killed.append(f'{check}:{name}')
  935      return killed
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

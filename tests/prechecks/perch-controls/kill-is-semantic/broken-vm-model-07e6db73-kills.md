<!-- prechecks packet v1; rule=kill-is-semantic; increment=vm-model; head=07e6db733079; base=cea554abc93f; builder=scripts/prechecks/packets@3a2ef420dff1; sources: vm/check-model.py@07e6db73 sha256=1f45bd478b9a9afe0320d678d1d1a2d2c9356dce5df46f722ecd6d0bca94eae8 -->
# Claim
Statements about what counts as a kill:

- docs/compiler-campaign/GATES.md: It builds the Bend model of `knot-vm-1` in `vm/model/` ([vm/MODEL.md](../../vm/MODEL.md)) with the seed's native lane and requires: the goldens to be their frozen plans' encodings and the `vm/LAWS.bend` fixtures their words; the model's prim and foreign tables to equal `vm/registry.json`; no Base `Bool.or` or `Bool.xor` in the natively built model, and `vm/model-lanes.bend` to print W's connectives as the comparisons' values on both seed lanes; all 93 golden runs and 44 frozen Book invocations to agree with `vm/golden/vm-expected.json`; 90 literal fuel controls and six inspection controls; the 72 frozen refusal controls (byte-level, both sides of SPEC section 4's resource limits, `Exhausted` kind 2 past one, and plan-level) and a child-at-parent boundary refused with check-spec's exact reason; the 13 argument controls; 66 admitted controls (vm-spec's six admitted plan, one limit, seven code-list and 41 run controls, each run control at its frozen fuel, and the model's own eleven, eight of them in `vm/model-controls/`, whose values the seed prints) run to their frozen or reference outcome and call count; the RC audit before every transition of every golden and zero live mortal cells after each completed run, with the reference evaluation's call count; the bounded soundness sweep, every single-word mutation of every golden refused exactly when the reference codec refuses it, for the same reason, and otherwise run soundly; `vm/PROOF.bend` printing `All terms check.` (32 laws); 46 model mutants killed by a wrong observation, never a crash or a harness fault, 14 of them also refuted by a law; and the harness mutant `fuel-ignored` killed by exactly the fuel controls.
- vm/MODEL.md: The probe does not kill those two mutants: there the comparison reaches Base's connective only through W's parameter, which the native lane reads correctly. - A Case arm that is absent or not a Branch or Default cannot be selected in an admitted image; if it were, the machine stops as `InternalFailure vm case arm` rather than reading a wrapped offset. - The gate stages every image its runs share (inspection, refusal, admitted and argument controls) once, before any run: a temporary file, made read-only and renamed into place.
- vm/MODEL.md: A refusal as `length`, `magic`, `total` or `noncanonical` of an image the reference codec admits is a harness fault, never a kill, and fails the gate.
- vm/MODEL.md: Before review round 3 the inspection images were rewritten on every run, and torn reads from concurrent mutants were counted as kills. - Deep lists recurse without a tail call (`pack`, `slice`); compiler-sized images are unmeasured.

# Evidence
`vm/check-model.py:301-303` function `well_formed`:
```python
  301  def well_formed(result) -> bool:
  302      """A model answer, not a crash, trap or timeout: those never count as a kill."""
  303      return result['exit'] in KNOWN_EXITS and 'bend:' not in result['stderr']
```

`vm/check-model.py:527-540` function `admitted_runs`:
```python
  527  def admitted_runs(model: Path, audit: Path, listed: list, argv=control_argv) -> dict:
  528      """Each admitted control's run at its fuel, its RC audit and its entries paid for."""
  529      def one(item):
  530          label, path, plan, fuel, want, calls = item
  531          result = run(argv(model, path, plan, fuel), 120)
  532          audited = run(argv(audit, path, plan, fuel), 300)
  533          m = AUDIT.match(audited['stdout'].strip())
  534          balanced = bool(m) and audited['exit'] == 0 and m.group(1) == 'passed' and (
  535              'exit' not in want or m.group(4) == '0') and int(m.group(5)) == calls
  536          # A kill is judged on the observation that went wrong.
  537          return label, {'result': audited if agrees(want, result) else result, 'admitted': True,
  538                         'agrees': agrees(want, result) and balanced, 'calls': int(m.group(5)) if m else None}
  539      with ThreadPoolExecutor(max_workers=8) as pool:
  540          return dict(pool.map(one, listed))
```

`vm/check-model.py:549-561` function `harness_runs`:
```python
  549  def harness_runs(model: Path, audit: Path, admitted: list, base: dict) -> list:
  550      """`fuel-ignored` runs every control at 1,000,000: exactly the fuel controls whose frozen
  551      run differs from the reference evaluation's at 1,000,000 must kill it, never a harness
  552      fault."""
  553      runs = [a for a in admitted if a[0].startswith('run:')]
  554      killers = sorted(label for label, path, plan, fuel, want, calls in runs
  555                       if fuel != cs.VM_FUEL and cs.ran(plan, {**want, 'calls': calls}) != {**want, 'calls': calls})
  556      got = admitted_runs(model, audit, runs, fuel_ignored)
  557      faults = harness_faults({'admitted': got})
  558      require(not faults, f'harness mutant fuel-ignored: harness faults, not kills, at {faults[:8]}')
  559      killed = sorted(n for n, r in got.items() if not r['agrees'] and base[n]['agrees'])
  560      require(killers and killed == killers, f'harness mutant fuel-ignored: killed by {killed}, the fuel controls {killers}')
  561      return [{'mutant': 'fuel-ignored', 'breaks': 'each run control runs at 1,000,000, not its frozen fuel', 'by': killed}]
```

`vm/check-model.py:850-867` function `harness_controls`:
```python
  850  def harness_controls(bins: dict, shared: dict) -> dict:
  851      """The mutant pool's reading of staged images, on the unmutated model: three workers run
  852      every staged run at once and every row agrees. A torn image (empty, a short prefix, a
  853      word-aligned prefix of value-on) is a harness fault that `kills` never credits."""
  854      with ThreadPoolExecutor(max_workers=3) as pool:
  855          rounds = list(pool.map(lambda _: staged_runs(bins, shared), range(3)))
  856      differ = sorted({f'{check}:{name}' for got in rounds for check, rows in got.items()
  857                       for name, row in rows.items() if not row['agrees']})
  858      require(not differ, f'harness control: concurrent staged runs disagree at {differ[:8]}')
  859      image = (GOLDEN / 'value-on.kimg').read_bytes()
  860      paths = staged('torn', [('empty', b''), ('short', image[:64]), ('prefix', image[:128])])
  861      torn = {'torn': {label: {'result': run([bins['model'], '--', path, 'main', '1000000'], 120), 'agrees': False,
  862                               'admitted': True} for label, path in paths.items()}}
  863      faults = harness_faults(torn)
  864      require(len(faults) == len(paths) and not kills({'torn': {label: {'agrees': True} for label in paths}}, torn),
  865              f'harness control: torn images {torn}')
  866      return {'concurrent': {'workers': 3, 'rows': sum(len(rows) for rows in rounds[0].values()), 'disagreements': 0},
  867              'torn': {label: model_refusal(row['result']) for label, row in torn['torn'].items()}}
```

`vm/check-model.py:1042-1045` function `law_kill`:
```python
 1042  def law_kill(tree: Path) -> str | None:
 1043      result = run([SEED, tree / 'vm' / 'PROOF.bend'], 1800)
 1044      found = re.search(r'Location: LAWS\.(\w+)', result['stdout'] + result['stderr'])
 1045      return found.group(1) if result['exit'] not in (0, None) and found else None
```

`vm/check-model.py` constant:
```python
KNOWN_EXITS = {0, 3, 4, 5, 6, 7}
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

<!-- prechecks packet v1; rule=expectation-independent; increment=vm-model; head=07e6db733079; base=cea554abc93f; builder=scripts/prechecks/packets@3a2ef420dff1; sources: vm/check-model.py@07e6db73 sha256=1f45bd478b9a9afe0320d678d1d1a2d2c9356dce5df46f722ecd6d0bca94eae8 -->
# Claim
Statements about where expected values come from:

- docs/compiler-campaign/GATES.md: It builds the Bend model of `knot-vm-1` in `vm/model/` ([vm/MODEL.md](../../vm/MODEL.md)) with the seed's native lane and requires: the goldens to be their frozen plans' encodings and the `vm/LAWS.bend` fixtures their words; the model's prim and foreign tables to equal `vm/registry.json`; no Base `Bool.or` or `Bool.xor` in the natively built model, and `vm/model-lanes.bend` to print W's connectives as the comparisons' values on both seed lanes; all 93 golden runs and 44 frozen Book invocations to agree with `vm/golden/vm-expected.json`; 90 literal fuel controls and six inspection controls; the 72 frozen refusal controls (byte-level, both sides of SPEC section 4's resource limits, `Exhausted` kind 2 past one, and plan-level) and a child-at-parent boundary refused with check-spec's exact reason; the 13 argument controls; 66 admitted controls (vm-spec's six admitted plan, one limit, seven code-list and 41 run controls, each run control at its frozen fuel, and the model's own eleven, eight of them in `vm/model-controls/`, whose values the seed prints) run to their frozen or reference outcome and call count; the RC audit before every transition of every golden and zero live mortal cells after each completed run, with the reference evaluation's call count; the bounded soundness sweep, every single-word mutation of every golden refused exactly when the reference codec refuses it, for the same reason, and otherwise run soundly; `vm/PROOF.bend` printing `All terms check.` (32 laws); 46 model mutants killed by a wrong observation, never a crash or a harness fault, 14 of them also refuted by a law; and the harness mutant `fuel-ignored` killed by exactly the fuel controls.
- docs/compiler-campaign/GATES.md: Every image its runs share is staged once, read-only, before any run; a refusal of an image the reference codec admits as `length`, `magic`, `total` or `noncanonical` is a harness fault that fails the gate, and a harness control runs every staged run three at once on the unmutated model and requires every row to agree.
- vm/MODEL.md: ## Commands ```sh S=scripts/bend-reference $S vm/model-cli.bend -o .local/vm-model/model # IMAGE FN FUEL [ORDINALS...] | IMAGE FUEL -- [ARGS...] $S vm/model-audit.bend -o .local/vm-model/audit # same arguments; RC audit before every transition, and calls $S vm/model-sweep.bend -o .local/vm-model/sweep # IMAGE FUEL; soundness of every single-word mutation $S vm/model-lanes.bend -o .local/vm-model/lanes # W.or and W.xor against Base's, on the native lane .local/vm-model/model -- vm/golden/closure-captures.kimg main 1000000 $S vm/PROOF.bend # All terms check. python3 vm/check-model.py # gate vm-model ```
- vm/MODEL.md: ```sh S=scripts/bend-reference $S vm/model-cli.bend -o .local/vm-model/model # IMAGE FN FUEL [ORDINALS...] | IMAGE FUEL -- [ARGS...] $S vm/model-audit.bend -o .local/vm-model/audit # same arguments; RC audit before every transition, and calls $S vm/model-sweep.bend -o .local/vm-model/sweep # IMAGE FUEL; soundness of every single-word mutation $S vm/model-lanes.bend -o .local/vm-model/lanes # W.or and W.xor against Base's, on the native lane .local/vm-model/model -- vm/golden/closure-captures.kimg main 1000000 $S vm/PROOF.bend # All terms check. python3 vm/check-model.py # gate vm-model ```

# Evidence
`vm/check-model.py:367-383` function `fuel_runs`, which builds expected values:
```python
  367  def fuel_runs(model: Path, expected: dict) -> dict:
  368      """SPEC section 7: every run starts with an entry, which fuel 0 cannot pay;
  369      value-on's `main` returns a nullary value after exactly one entry."""
  370      cases = {n: c for n, c in expected['cases'].items() if c.get('outcome') != 'Unsupported'}
  371      want = {n: ('Exhausted', 'vm', '1', 'fuel') for n in cases}
  372      jobs = [(n, fuel_argv(c, '0')) for n, c in cases.items()] + [('value-on@1', fuel_argv(cases['value-on'], '1'))]
  373      with ThreadPoolExecutor(max_workers=8) as pool:
  374          got = dict(zip([j[0] for j in jobs],
  375                         pool.map(lambda j: run(argv_of(model, j[0].split('@')[0], j[1]), 120), jobs)))
  376      out = {}
  377      for n, result in got.items():
  378          if n == 'value-on@1':
  379              good = (result['exit'], result['stdout']) == (0, 'Evaluated\t0\t1\tOn{}\n')
  380          else:
  381              good = result['exit'] == 4 and tuple(result['stderr'].rstrip('\n').split('\t')) == want[n]
  382          out[n] = {'result': result, 'agrees': good, 'admitted': True}
  383      return out
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

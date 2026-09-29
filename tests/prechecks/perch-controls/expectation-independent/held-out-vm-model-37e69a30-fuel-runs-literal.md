<!-- prechecks packet v1; rule=expectation-independent; increment=vm-model; head=37e69a30e242; base=229191879a59; builder=scripts/prechecks/packets@3a2ef420dff1; sources: vm/check-model.py@37e69a30 sha256=f3323df6af46ab44ad12801d71721a80ecb3eefad2a5816402e5b775bb2d01a8 -->
# Claim
Statements about where expected values come from:

- docs/compiler-campaign/GATES.md: It builds the Bend model of `knot-vm-1` in `vm/model/` ([vm/MODEL.md](../../vm/MODEL.md)) with the seed's native lane and requires: the goldens to be their frozen plans' encodings and the `vm/LAWS.bend` fixtures their words; the model's prim and foreign tables to equal `vm/registry.json`; all 91 golden runs and 28 frozen Book invocations to agree with `vm/golden/vm-expected.json`; literal fuel and inspection controls; the 61 frozen refusal controls and a child-at-parent boundary refused with check-spec's exact reason; 25 admitted controls (vm-spec's three admitted plan, seven code-list and seven run controls, and the model's own eight in `vm/model-controls/`, whose values the seed prints) run to the reference evaluation's outcome and call count; the RC audit before every transition of every golden and zero live mortal cells after each completed run, with the reference evaluation's call count; the bounded soundness sweep, every single-word mutation of every golden refused exactly when the reference codec refuses it, for the same reason, and otherwise run soundly; `vm/PROOF.bend` printing `All terms check.`; and 24 model mutants killed by a wrong observation, never a crash, seven of them also refuted by a law of `vm/PROOF.bend`.
- vm/MODEL.md: ## Commands ```sh S=scripts/bend-reference $S vm/model-cli.bend -o .local/vm-model/model # IMAGE FN FUEL [ORDINALS...] | IMAGE FUEL -- [ARGS...] $S vm/model-audit.bend -o .local/vm-model/audit # same arguments; RC audit before every transition, and calls $S vm/model-sweep.bend -o .local/vm-model/sweep # IMAGE FUEL; soundness of every single-word mutation .local/vm-model/model -- vm/golden/closure-captures.kimg main 1000000 $S vm/PROOF.bend # All terms check. python3 vm/check-model.py # gate vm-model ```
- vm/MODEL.md: ```sh S=scripts/bend-reference $S vm/model-cli.bend -o .local/vm-model/model # IMAGE FN FUEL [ORDINALS...] | IMAGE FUEL -- [ARGS...] $S vm/model-audit.bend -o .local/vm-model/audit # same arguments; RC audit before every transition, and calls $S vm/model-sweep.bend -o .local/vm-model/sweep # IMAGE FUEL; soundness of every single-word mutation .local/vm-model/model -- vm/golden/closure-captures.kimg main 1000000 $S vm/PROOF.bend # All terms check. python3 vm/check-model.py # gate vm-model ```
- vm/MODEL.md: ```sh S=scripts/bend-reference $S vm/model-cli.bend -o .local/vm-model/model # IMAGE FN FUEL [ORDINALS...] | IMAGE FUEL -- [ARGS...] $S vm/model-audit.bend -o .local/vm-model/audit # same arguments; RC audit before every transition, and calls $S vm/model-sweep.bend -o .local/vm-model/sweep # IMAGE FUEL; soundness of every single-word mutation .local/vm-model/model -- vm/golden/closure-captures.kimg main 1000000 $S vm/PROOF.bend # All terms check. python3 vm/check-model.py # gate vm-model ``` The seed runtime strips its own options up to the first `--`, so callers put `--` before the image.

# Evidence
`vm/check-model.py:234-250` function `fuel_runs`, which builds expected values:
```python
  234  def fuel_runs(model: Path, expected: dict) -> dict:
  235      """SPEC section 7: every run starts with an entry, which fuel 0 cannot pay;
  236      value-on's `main` returns a nullary value after exactly one entry."""
  237      cases = {n: c for n, c in expected['cases'].items() if c.get('outcome') != 'Unsupported'}
  238      want = {n: ('Exhausted', 'vm', '1', 'fuel') for n in cases}
  239      jobs = [(n, fuel_argv(c, '0')) for n, c in cases.items()] + [('value-on@1', fuel_argv(cases['value-on'], '1'))]
  240      with ThreadPoolExecutor(max_workers=8) as pool:
  241          got = dict(zip([j[0] for j in jobs],
  242                         pool.map(lambda j: run(argv_of(model, j[0].split('@')[0], j[1]), 120), jobs)))
  243      out = {}
  244      for n, result in got.items():
  245          if n == 'value-on@1':
  246              good = (result['exit'], result['stdout']) == (0, 'Evaluated\t0\t1\tOn{}\n')
  247          else:
  248              good = result['exit'] == 4 and tuple(result['stderr'].rstrip('\n').split('\t')) == want[n]
  249          out[n] = {'result': result, 'agrees': good}
  250      return out
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

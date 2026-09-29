<!-- prechecks packet v1; rule=kill-is-semantic; increment=vm-model; head=19cf7d8f71ff; base=none; builder=manual-excerpt@47dbd98ca1c7; sources: docs/COMPILER-CAMPAIGN.md@19cf7d8f sha256=40e00d3b2f87172cf12890ff2fb1561395b84165009a65be9d0c0d56c46d8b7a; vm/check-model.py@19cf7d8f sha256=f9d4dd03a9050086e0f05b793c504480690a6c8fe5fe27593f71f935d2901f77 -->
# Claim
`docs/COMPILER-CAMPAIGN.md:41-44` (trusted-runtime definition of done)

>      - VM ⇔ model after every transition on small images;
>      - VM ⇔ `src/eval.bend` ⇔ seed on the values of every frozen suite, where Exhausted excuses a lane only under a documented bound;
>      - mutants killed by named gates.
>    - **Names.** C1 means "compiler, generation 1": the upstream seed builds Knot's own Bend source into a runnable compiler. It is not the C language, and not the `knot-c-1` backend.

# Evidence
`vm/check-model.py:598-609` (function inspection_runs, named by the design table)

```
  598  def inspection_runs(model: Path) -> dict:
  599      folder = BUILD / 'inspection'
  600      folder.mkdir(parents=True, exist_ok=True)
  601      out = {}
  602      for name, plan in INSPECTION.items():
  603          data = codec.encode(plan, DIGEST)
  604          require(cs.rejected(data, REGISTRY, DIGEST) is None, f'{name}: the reference codec refuses it')
  605          got = reference.book(plan, 'main', [], 1000000)
  606          require({k: got.get(k) for k in cs.ILL_TYPED} == cs.ILL_TYPED, f'{name}: the reference evaluation gives {got}')
  607          path = folder / f'{name}.kimg'
  608          path.write_bytes(data)
  609          result = run([model, '--', path, 'main', '1000000'], 120)
```

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

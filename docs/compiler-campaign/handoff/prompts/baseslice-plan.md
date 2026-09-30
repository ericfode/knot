# baseslice: the plan for the Base library slice, then its first step

**Why this matters.** On main, the self-hosting gate (`tests/compiler-selfhost`, receipt `tests/compiler-selfhost/receipts/selfhost.json`) passes 2 of 65 cases. **48** of the 63 blocked cases name `base` as a blocker, making it the largest single blocker. `campaign/baseslice` (ff44b974, 2026-09-27) holds an earlier Base-slice increment, which has not been examined against the self-hosting route (D14, VM-first) since.

1. Merge `main` (5571625f or later) with a merge commit, and get `npm run -s gates` green, fixing anything the merge broke.
2. **Analyse** and write `docs/compiler-campaign/BASE-SLICE-PLAN.md`:
   - (a) what the selfhost judge means by `base`, from the judge's code, not from the label;
   - (b) exactly which Base declarations Knot's own `src/*.bend` reaches, transitively; list them with their shapes (datatypes, functions, generics, closures, IO, primitives);
   - (c) what campaign/baseslice already provides, and what main provides;
   - (d) for each reachable Base declaration: what Knot needs to check it, evaluate it, lower it to the core and encode it in a VM image (`vm/SPEC.md`), and which unmerged increment it waits on (nest, literals, generics, closures, modules);
   - (e) an ordered list of increments, each with its size, dependencies, acceptance criteria, the seed-derived expectations to freeze (D7) and the mutants.
3. **Implement** the first increment of the plan that depends on no unmerged branch, with frozen seed expectations, mutants and a gate registered in `scripts/gates/run.py`. Stop when that increment is complete and the gates pass.

Report the plan's headline numbers (reachable declarations, how many are covered and by whom), the increment you implemented, and every gate's exact counts.

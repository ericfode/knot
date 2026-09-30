# BS1: the Base enum source island

This is the first independent step of
[BASE-SLICE-PLAN.md](../../../docs/compiler-campaign/BASE-SLICE-PLAN.md).
It qualifies the existing compiler on seven verbatim declarations from the
unmodified pinned Base: Unit, Bool, Cmp, Bool.not, Bool.and, Bool.or and Cmp.is_eq.
It adds no loader, checker bypass or source-language capability. Production
`import Base` remains Unsupported until the modules increment is integrated.

```sh
export BEND_NO_TELEMETRY=1
python3 -B tests/compiler-baseslice/enum/regen.py
python3 -B tests/compiler-baseslice/enum/check.py
npm run -s gates -- --jobs=1
```

The gate is `base-enum` in `scripts/gates/run.py`. Builds, wrappers, mutants and
generated modules live under ignored `.local/baseslice/enum/`. Its durable
receipt is [receipts/enum.json](receipts/enum.json).

The oracle was committed in **3b32cc4c**, before the runner. It fixes seven books,
32 seed calls on interpreter and native lanes, exact source hashes, Base line
spans and digest, constructor order, call arguments and seed rejection reasons.
`regen.py --write` changes only observations and requires two identical freezes;
it is an explicit oracle amendment, never part of `check.py`.

The seed requires `import Base` for native builds and reserves Base names even
in imported modules. Its oracle therefore loads unmodified Base with the same
consumer body. Knot receives the seven exact declaration excerpts followed by
that body. The oracle stores both representations and checks the excerpt bytes.
The positive source qualification books deliberately contain no import. This
distinction does not qualify Base loading or name registration.

The two positive books cover 31 calls: 21 Boolean observations and ten Cmp/Unit
observations. A native-built and a Bun-built Knot each check the books, evaluate
every call and emit actual Wasm that Node validates and executes. The modules
must be byte-identical across compiler builds. Four negative books pin affine
reuse, type mismatch, wrong call arity and a missing Bool arm. A fifth, seed-valid
book pins the current Unsupported import boundary. Check, eval and compile must
all report the expected refusal, create no fresh output and preserve an existing
output in both compiler builds.

Eight source-algebra laws have checked fills and zero holes: five universal
finite-domain laws and three ground Cmp equations. They prove the source algebra,
not compiler refinement. The trust audit retains the seed's whole loaded Base
unsafe and foreign inventory separately from execution reach.

Five type-correct compiler mutants attack constant tags, inverted case choice,
argument-slot aliasing, constant evaluation and the type boundary. Each must
build and exhibit its specified classified disagreement with an unchanged
fixture. Crashes, build errors, timeouts and invalid Wasm cannot count as kills.
The mutated compiler sources stay in this worktree's ignored scratch directory.

The [law review](LAW_REVIEW.md) records observations, witnesses and limits.
The original forty-book baseslice suite remains frozen and separate. VM images,
module integration, generics, literals, closures and IO are subsequent steps.
Live semantic/style Perch reviews are unrun under the implementer's instructions.

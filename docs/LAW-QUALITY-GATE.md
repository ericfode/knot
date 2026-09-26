# Law quality and publication gate

Applies to the compiler-support package campaign requested on 2026-09-26.
The user authorized implementation, iterative Perch improvements, and publication
of completed packages to Bend's package hub. Proof quality is part of completion.

The target is adequate specification of the declared public contract. Neither
test count nor a model score proves that an arbitrary specification is complete.
Use the following evidence to make adequacy reviewable and to expose omissions.

## Required evidence

1. **Contract before optimization.** Write `SPEC.md`: abstract values, observable
   behavior, public operations, success/failure semantics, ownership, identifier
   lifetime, domain bounds, and complexity targets. Separate implementation
   details from what callers may rely on.
2. **Independent model.** Prefer a deliberately simple list/map/state model.
   State the abstraction relation between optimized storage and that model.
   Behavioral laws must reach public observations; a model proven correct in
   isolation does not establish refinement by the public implementation.
3. **Inhabited domains.** For every behavioral law, construct witnesses satisfying
   its domain and antecedents. Include nonempty and nontrivial witnesses where
   relevant. An impossible precondition, Empty parameter, contradictory invariant,
   or unsafe inhabitant cannot establish useful behavior. Invalid-input laws need
   invalid-input witnesses. Auxiliary tautologies must be labeled auxiliary.
4. **Observable essence.** Ask whether a constant, input-discarding, order-reversing,
   or stale-state implementation could satisfy the claimed behavioral laws.
   Specify values, order, identity, state preservation, and failures that define
   the component. Length and representation validity alone are rarely enough.
   Conversely, element contents alone may be insufficient: a list projection
   that drops empty slots can hide a stale public length or wrong bounds result.
   Cover every promised public observation and the coherence between them.
5. **Coverage matrix.** Map every exported operation to laws, independent runtime
   checks, relevant domain partitions, and source locations. Cover operation
   composition and preservation of unrelated state. Enumerate explicit omissions;
   never count unimplemented or unexported features as covered functionality.
6. **Truthful proof boundary.** `LAWS.bend` states the contract and `PROOF.bend`
   fills it. Run the pinned compiler on the complete proof entry and require
   zero holes. Do not use `?TODO`, new axioms, or `@unsafe` to get a gate green.
   Inventory native/unsafe transitive dependencies. Distinguish universal proofs,
   bounded exhaustive checks, concrete normalization, and runtime tests. Preserve
   this distinction when a universal theorem is difficult; improve it instead
   of silently advertising a few literal equations as a universal proof.
   Negative compile tests must reach the intended checker phase and match the
   intended diagnostic. Pair a failing ownership/type fixture with a nearby
   valid control when syntax is uncertain. A parser failure or generic nonzero
   exit does not establish an ownership/type restriction.
7. **Semantic mutation tests.** Deliberately break the defining behavior while
   keeping the implementation parseable and type-correct. Exhibit a witness for
   the violated contract. The unchanged laws or independent assertions must kill
   that mutant for the expected reason. Also attack a boundary and a composition
   property where applicable. Record survivors and equivalent mutants separately.
   Parse/type failures, missing imports, timeouts, and harness failures are not
   semantic kills. Do not weaken a law just to make the implementation pass.
   Record the intended violated observation and the actual rejecting law or
   assertion separately when another relevant assertion fails first.
8. **Performance evidence.** Run increasing workloads with result equivalence and
   operation/allocation counts where available. Check the promised complexity
   and native lowering. Report timings separately from proofs. Test only targets
   claimed by the package; a native run does not establish GPU execution.
9. **Independent review pass.** Re-read the contract and laws as a hostile caller:
   identify an allowed behavior that would make the package useless, then attempt
   to construct it. Record the candidate, outcome, remaining scope, and exact
   source hashes in `LAW_REVIEW.md`. This is a review, not a formal completeness
   theorem. Request bounded sidecar review only when authorized by local workflow.
10. **Release exactly what was checked.** Freeze file hashes and dependency pins,
    rerun proof/conformance/mutation gates, inspect the actual upload closure,
    publish, then fetch into a fresh Bend cache and compile/run a consumer of
    the returned hash. Keep the upload response and consumer receipt. A proposed
    hash or an HTTP success without matching package identity is not publication.

## Perch workflow

The eight `law-*` rules in `.perch/rules/laws.yaml` review bounded packets named
`LAW_REVIEW.md` under a package, optionally one subdirectory per operation family.
A packet includes the relevant signatures, contract observations, law statements,
witness constructors, abstraction relation, proof/test/mutation evidence, and
source hashes. Do not expect a file-only model check to follow links to unseen
proofs. Keep each packet small enough for a complete reading and disclose any
omitted implementation context. The top-level packet indexes the API matrix.

Use working-copy checks, for example:

```sh
npm run lint -- packages/vec/LAW_REVIEW.md --rules law-domain-inhabited,law-observable-essence,law-public-contract-coverage,law-independent-model,law-state-composition,law-boundaries-and-exhaustion,law-mutation-sensitivity,law-proof-claim-integrity --json
```

Require a nonzero relevant-rule count and a complete request. Perch 0.3.5 has no
Bend method parser; a successful zero-coverage scan is not useful. `check` may
exit 3 for an advisory finding; inspect its JSON. Provider/config failures are
neither passes nor defects in the package.

Each package author owns `.perch/rules/package_<package>.yaml` and paired rule
controls under that package. Turn a repeated mistake into a narrow rule; give it
a clean control, the specific broken control, and a held-out example. Record the
model, inputs/hashes, raw probabilities, coverage, and observed separation. Refine
rules that cannot separate the cases; do not merely increase a threshold. Keep
them advisory until calibrated. Do not copy common rules under duplicate names.

At campaign setup no Perch API key was configured. Rule syntax can be validated;
live model calibration must be recorded as unavailable until credentials exist.
Common draft-rule controls are in `tests/perch-laws/cases.json`; the offline
`node scripts/check-law-rule-wiring.mjs` verifies selectors and request coverage.
It substitutes fixed probabilities and cannot measure rule quality.
Continue deterministic implementation, review, proof and mutation work. A model
verdict is not a publication authorization or a substitute for this gate.

## Package evidence layout

- `SPEC.md`, `INTERFACE.md`: behavior and stable dependency interface.
- `main.bend`, `model.bend`, `LAWS.bend`, `PROOF.bend`: implementation, independent
  model, statements, and proofs; split implementation modules when helpful.
- `conformance.bend`, `example.bend`, `tests/`, `scripts/`: runnable checks,
  semantic mutants, performance probes, and reproducible gate commands.
- `LAW_REVIEW.md` and optional family packets: matrix, domains, witnesses,
  adversarial review, and results, with precise claim categories.
- `STATUS.md`: actual state, interface stability, dependencies, next step,
  blockers and gate receipts. Other chats may read it but only its owner edits it.
- `RELEASE.json`: pinned compiler/dependencies, source/closure hashes, gate
  outcomes, license, hub response/hash, published import, and fresh-consumer result.

Publish from a reviewed entry that includes the intended laws/proofs in the
uploaded transitive closure. Checking a local `PROOF.bend` does not automatically
upload it when publishing `main.bend`. Choose a publication entry and document
the resulting import paths. Avoid circular imports; a proof/release entry may
import implementation and law modules while consumers import the included API.

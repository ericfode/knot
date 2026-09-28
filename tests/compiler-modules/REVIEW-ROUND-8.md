# Modules review round 8

Round 8 reviewed `05d906b` and confirmed two major findings. Both predate this
branch. Main (`c0bd08d`) shows each one in the single-file lane, and the bundle
lane inherits it because every module body passes through the same parser and
catalog. A sibling branch that is not merged here fixes each one.

Neither finding is repaired on this branch. This round changes no source,
fixture, expectation, law or gate assertion. It records the dispositions, the
reproduction and the obligations for the reconciliation rounds.

| Finding | Fixed on | Disposition |
| --- | --- | --- |
| A constructor brace detached from its name (`On {}`) is accepted in the bundle lane (major, soundness) | `campaign/nest` `43d6553`, "Reject a constructor brace detached from its name" | **Deferred to the post-nest reconciliation round.** The finding's fix reads "Make no repair on this branch", and the round-7 decision keeps nest's files out of this branch. |
| An empty datatype in a user file is `Invalid check empty-datatype`, but the seed accepts it (major, D4) | `campaign/generics` `88e204b` reports it Unsupported; `campaign/nest` `997f83f`/`57a0c01` accept it | **Deferred. The prescribed rule is disputed and needs a coordinator decision.** The fix prescribes generics' rule. Nest merges first, accepts empty datatypes, and states a contradictory law of the same name ([below](#finding-2-the-prescribed-rule-is-disputed)). |

## Reproduction

All builds use the pinned seed:

- this branch at `05d906b`, native and Bun;
- `campaign/nest` at `e0db57e`, single-file check and eval;
- `campaign/generics` at `edfad8b`, single-file check.

The nest and generics builds come from `git archive`. The probes are the
reviewer's, copied unchanged, plus `sf-absurd`, a single-file form of
`em-absurd`. The runner, probes, transcripts and merge simulations are in
`.local/modules/r8/`.

**Finding 1** (`r8-detached.txt`):

| Probe | Seed | This branch, bundle: check native, Bun; eval | This branch, single file | Nest, single file |
| --- | --- | --- | --- | --- |
| `spm-mod` (`On {}` in a module body) | exit 1, `observed : '{'` | Checked, Checked, `Lit{}` | `Unsupported parse import` | `Unsupported parse import` |
| `spm-entry` (`case M.Off {}`, `see(M.On {})`) | exit 1, `observed : '}'` | Checked, Checked, `Lit{}` | `Unsupported parse import` | `Unsupported parse import` |
| `spm-base` (`Bool.not(False {})`) | exit 1, `observed : '}'` | Checked, Checked, `Lit{}` | `Unsupported parse declaration-form` | `Unsupported parse declaration-form` |
| `sp/ret-space`, `main-space`, `pattern-space`, `arg-space` | exit 1 | Checked, Checked, `Lit{}` | Checked | `Invalid parse detached-brace` |
| `sp/call-space`, `decl-space`, `def-space` (controls) | exit 0, `Lit{}` | Checked, Checked, `Lit{}` | Checked | Checked, `Lit{}` |

**Finding 2** (`r8-empty-bundle.txt`, `r8-empty-single.txt`):

| Probe | Seed | This branch, bundle: native, Bun, eval | This branch, single file | Nest, single file | Generics, single file |
| --- | --- | --- | --- | --- | --- |
| `tc2`, `em-absurd`, `em-param`, `em-hash` (empty type in an imported module) | exit 0, `Lit{}` | `Invalid check empty-datatype` | `Unsupported parse import` | `Unsupported parse import` | `Unsupported parse import` |
| `em-entry`, `sf-empty/{main,mid,data}`, `sf-absurd` (empty type in the entry) | exit 0, `Lit{}` | `Invalid check empty-datatype` | `Invalid check empty-datatype` | Checked, `Lit{}` | `Unsupported check empty-datatype` |
| `empty-param` (Base `Empty`) | exit 0, `Lit{}` | `Unsupported check base-empty-datatype` | `Unsupported parse declaration-form` | same | same |

## Finding 2: the prescribed rule is disputed

- **Nest accepts.** Its `catalog.datatype` returns `Done` for zero constructors.
  Its `law empty_datatype` states `G.datatype(Nil{},name,data) ==
  Done{C.Datatype{name,data,Nil{}}}`. On every entry probe above, nest agrees
  with the seed, including the zero-arm `match` in `absurd`.
- **Generics reports Unsupported.** Its `catalog.nonempty` returns
  `Unsupported check empty-datatype`. Its `law empty_datatype` states
  `G.nonempty(Nil{},name,data) == Fail{S.Unsupported{"check","empty-datatype",…}}`.
- **The two rules collide at merge.** A simulated merge
  (`git merge-tree --write-tree campaign/nest campaign/generics`) conflicts in
  `catalog.bend`. It merges `catalog-LAWS.bend` and `catalog-PROOF.bend`
  without a textual conflict, which leaves two contradictory
  `law empty_datatype` declarations and two fills
  (`nest-generics-empty-laws.txt`). The coordinator chooses the rule at that
  junction.
- **This branch is not the conflict.** The finding expects generics' rule to
  conflict with the round-7 edits to `catalog.bend`. But
  `git merge-tree --write-tree HEAD campaign/generics` merges `catalog.bend`,
  `catalog-LAWS.bend` and `catalog-PROOF.bend` without conflict
  (`mt-generics-before.txt`). The collision is between nest and generics.
- **Porting either rule here adds a conflict.** `catalog.bend` merges cleanly
  with nest today, and would conflict if `nonempty` were edited.
  `catalog-LAWS.bend` already conflicts with nest, where round 7 and nest each
  added a law after `field_capability_is_not_acceptance`
  (`mt-nest-before.txt`, `mt-generics-before.txt`).

Both rules satisfy D4. Only the current `Invalid` violates it.

## Obligations for the reconciliation rounds

**Finding 1**, after nest reaches main and this branch merges main:

- Freeze `spm-mod`, `spm-entry` and `spm-base` from the pinned seed as
  modules-gate fixtures. Each expects `Invalid parse detached-brace` in both
  bundle lanes.
- The single-file lane reads no imports. On this branch and on nest it reports
  `spm-entry` as `Unsupported parse import`. To pin the entry's spellings
  through the single-file parser, also freeze an import-free variant
  (`case Off {}`, `see(On {})`).
- Add a bundle-lane mutant that ignores the touch, like nest's
  `ignore-detached-brace`. `spm-mod` kills it.

**Finding 2**, after the coordinator chooses the rule:

- Freeze `tc2`, `em-absurd`, `em-param`, `em-entry` and `em-hash` in both bundle
  lanes, and `sf-empty/{main,mid,data}` and `em-entry` in the single-file lane.
  Pin the chosen verdict exactly:
  - Nest's acceptance: `match-seed` with `requires: []`, which demands exit 0
    and the seed's `Lit{}` in evaluation and Wasm.
  - Generics' rule: `knot_expected` with the prefix
    `Unsupported\tcheck\tempty-datatype\t`.
  - Not `match-seed` with a nonempty `requires`. The gate then accepts any
    Unsupported code, so an unrelated one, such as `parse import`, would pass.
- Add a bundle-lane mutant that demotes the chosen rule to `Invalid`, with
  witness `tc2`.
- If the rule reaches this branch through main, the single-file lane matches
  main and needs no delta row. If it is applied here first, add a row under
  "single-file deltas" in `src/SPEC.md` and `tests/compiler-modules/SPEC.md`.
- `base-empty-datatype` stays for now:
  - The Base slice raises it before the catalog runs, at a Base location, so it
    names Base's `Empty` and not a user declaration.
  - Only its own law, `empty_base_type_is_unsupported`, pins it.
  - If the coordinator chooses acceptance, the same round decides whether Base's
    `Empty` is selected and accepted, and whether the two codes are aligned.

## Gates

On the tree of `e724f1d`, `npm run -s gates` passed all 22 gates, and
`gates:verify` ran 19 tests, OK. Because no source or fixture changed, every
count equals round 7's. The modules gate checked 191 fixtures, 199 seed calls,
53 mutants and 4 proof entries. The census counted 925 declarations in 44
files, and the bootstrap corpus held 1,075 files. No receipt was rewritten.
No Bend file changed, so there is nothing to preflight, and no style rating is
claimed.

## Carried over

- The round-7 nest reconciliation of dotted binders.
- Live Perch review.
- The selfhost `modules` and `packages` needs.
- Refreshing shared receipts after the merge.

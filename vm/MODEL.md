# The Bend model of `knot-vm-1`

`vm/model/` is the normative semantics of [SPEC.md](SPEC.md), written in the
I-profile from the spec text alone (no WAT exists on this branch). One idea
carries it: **the machine is a word store at SPEC addresses plus a few
registers, and every transition is a store update.** Cells, Activations and
the constant pool live in one store keyed by word address; the image is a
second, read-only store; frames are typed records whose word sizes match
§6's `[value[n], node, aux, head]` layout.

Seven sections, each importing only earlier ones, under the alias it is read by:

| Section | What it fixes |
|---|---|
| `word.bend` (`W`) | `none` and lazy choice, the word store (a most-significant-first trie; absent words read 0), little-endian packing, strict UTF-8, the plan, the stop type |
| `decode.bend` (`D`) | the §2 decoder, refusing in `serializer.decode`'s order and wording |
| `validate.bend` (`V`) | the registry tables and §4 rules 1-5, refusing in `serializer.validate`'s order and wording |
| `encode.bend` (`E`) | the §2 encoder, and the loader: decoded, validated and canonical |
| `memory.bend` (`H`) | §5 words and cells, power-of-two classes, LIFO free lists, bump allocation at the §5 heap base, uniform RC, the iterative release worklist bounded by the frame region, the loaded code, frames, §6 inspection, §9 prims |
| `machine.bend` (`M`) | §6's Eval/Return/Enter table, tail entry, Case selection, §7 fuel and quantum, §8 describe, booting (immortal constants, the terminal continuation), the Book invocation walk and Program phases, IO.print Actions |
| `audit.bend` (`A`) | `balanced` (rc equals owners among roots and edges; no word above an Activation's depth), `leaked` (mortal cells still live), and the law predicates |

[perch-manifest.json](perch-manifest.json) gives each section, the entries and
the laws a Perch composition group: the section in full, its collaborators as
interfaces (`interfaces-v1`), each under the 48,000-byte composition bound.

## Commands

```sh
S=scripts/bend-reference
$S vm/model-cli.bend -o .local/vm-model/model      # IMAGE FN FUEL [ORDINALS...] | IMAGE FUEL -- [ARGS...]
$S vm/model-audit.bend -o .local/vm-model/audit    # same arguments; RC audit before every transition, and calls
$S vm/model-sweep.bend -o .local/vm-model/sweep    # IMAGE FUEL; soundness of every single-word mutation
$S vm/model-lanes.bend -o .local/vm-model/lanes    # W.or and W.xor against Base's, on the native lane
.local/vm-model/model -- vm/golden/closure-captures.kimg main 1000000
$S vm/PROOF.bend                                   # All terms check.
python3 vm/check-model.py                          # gate vm-model
```

The seed runtime strips its own options up to the first `--`, so callers put
`--` before the image. Outcomes print as eval-cli does: `Evaluated` lines on
stdout; `Exhausted<TAB>vm<TAB>kind<TAB>cause` (exit 4), `HostFailure<TAB>phase<TAB>code`
(5), `Unsupported<TAB>phase<TAB>code` (3) and `InternalFailure<TAB>vm<TAB>code` (6) on
stderr. `HarnessBound<TAB>model<TAB>transitions` (7) is the model's own Nat bound
on transitions: a harness limit, never VM exhaustion.

## Laws

[LAWS.bend](LAWS.bend) states 29 laws, proved by [PROOF.bend](PROOF.bend):
- the codec round trip, on a hand-written plan and on five golden images;
- four refusal reasons, and bounded validator soundness: every single-word
  mutation of `value-on`'s function, constant and node sections is refused or
  runs soundly;
- symbolic machine equations over arbitrary states: an entry at fuel 0 is
  Exhausted, a finished machine is final, tail position, the Nat bounds, `x/0`,
  `x%0` and shifts by 32 or more;
- one audited run per fixture image (a Book per node family and a Program): its
  answer, the RC audit at every transition and zero live mortal cells after it;
- audited runs of plans encoded in the law: a tags-mode Case on Char selects
  Chr for the code of 'A'; a key-mode Case on Char admits and selects the key
  0xffffffff; a key Branch and a Default answer a `none` parameter in a U32 Case
  (arm fit, §3); a Nat word spells its type's own constructor names; and
  completing Chr on a laundered Pair stops `HostFailure image ill-typed` with
  every count balanced;
- §8's byte measure: `text_size` counts UTF-8 bytes, not scalars.

These are bounded computed equations, not a refinement proof. The gate
evaluates the same predicates natively on more images: the audit on every
golden and the soundness sweep over every single-word mutation (zero,
successor, predecessor) of every golden, diffed against `serializer.py`.

## Known limits and deltas

- Effects: only `IO.print` is modelled. Applying any other foreign Action is
  `Unsupported vm foreign N`; vm-io adds the pure World.
- Inspection reads every operand word of a prim at its pinned type, including
  `String.append`'s moved tail, whose cells it does not traverse.
- §8's describe charges one visit per rendered constructor (a Nat word `n`
  pays `n + 1`) and the tree's UTF-8 bytes with separators, both bounds
  inclusive, inspecting each word before charging it, as `evaluate.describe`
  does. A description that stops (a display bound or an ill-typed word) stops
  the machine with the answer still owned, like any refused transition; §8
  does not say whether it is dropped.
- Completing Chr inspects its operand at Char, used or not, as the reference
  evaluation's `construct` reads it; SPEC §6's list of inspection points does
  not yet name Succ's or Chr's operand.
- A Nat Case makes the predecessor only for a selected Succ Branch, after the
  Scope push, and moves it into its slot (§6.1): `nat-case-big` frees its Big
  predecessor and `nat-default-big` allocates none, both under the RC audit.
  With atomic steps (below) the push-first order shows only when the frame
  region and the heap are both full, which no control reaches.
- The command line reads the image first, then its entry kind's form (§8): a
  missing word, or a Program's second word other than `--`, is `HostFailure
  arguments usage` before any word is read; FUEL and each ordinal are Base's
  `U32.read` words (`expected-u32`). check-spec's 13 argument controls run in
  the gate.
- A refused transition leaves the machine as it was: the model's steps are
  atomic, including one refused mid-way by an allocation. An Enter's debit
  stands once paid (§7): a target that then stops the machine, such as D20's
  refused print, leaves its fuel and call spent.
- A stopped machine keeps the control it could not advance, so the words of a
  pending Enter stay owned (§7).
- The frozen eval suites have no images until the `image` encoder exists; the
  model's differential covers the 93 goldens, their 44 frozen Book invocations,
  vm-spec's admitted plan, code-list and run controls (counted from
  `check-spec.py`: 6, 7 and 23 at vm-spec c7250b2, each run control at the fuel
  frozen with it), its 13 argument controls, the model's own eight controls in
  [model-controls/](model-controls/) (a tags-mode Case on Char, immediate and
  Big, and key-mode Cases on U32 and Char at the key 0xffffffff), two display
  controls with multibyte constructor names at and beyond the byte bound, and
  six inspection controls, each against the reference evaluation's outcome and
  call count (`vm/evaluate.py`) and, for the seed-derived eight, the seed.
- The seed's native lane misreads a U32 comparison against a nullary call or a
  call with constant arguments when it is an operand of Base's `Bool.or` or
  `Bool.xor`: the comparison reads as True whatever its value. Either operand
  triggers it, the comparison's other side may be a runtime word, and
  `Bool.xor` fails even when its other operand is True
  (`Bool.xor(U32.is_gt(3,limit()),True{})` is 1 on the Bun lane and 0
  natively, with `limit() = 1048576`). A helper whose arguments become constant
  at a call site triggers it through specialization: review round 2 found
  `Bool.or(W.is_none(0),False{})` read as True. The emitted C shows why: the
  comparison is held as a raw word, `Term _u_N = U32_BIN(3ull, >, 1048576ull)`,
  and then tested as a constructor, `term_aux(_u_N) == CID_FALSE`
  (`comp.ts` `val_unbox`). `Bool.and`, `Bool.not`, `Bool.pick` and a choice's
  condition read the same comparisons correctly in every probed shape. These are
  probe results, not a proof of the seed's rule, so the protection is
  structural: the natively built model spells disjunction and exclusive or as
  choices (`W.or`, `W.xor`), the gate refuses Base's `Bool.or` and `Bool.xor`
  anywhere in it (the mutants `or-through-base` and `xor-through-base` die
  there), and [model-lanes.bend](model-lanes.bend) prints W's connectives on
  those shapes as the comparisons' values on both lanes while the native lane
  still misreads Base's. The probe does not kill those two mutants: there the
  comparison reaches Base's connective only through W's parameter, which the
  native lane reads correctly.
- A Case arm that is absent or not a Branch or Default cannot be selected in
  an admitted image; if it were, the machine stops as `InternalFailure vm case
  arm` rather than reading a wrapped offset.
- Deep lists recurse without a tail call (`pack`, `slice`); compiler-sized
  images are unmeasured. The checker's evaluator is slow: PROOF.bend takes
  about 95 s, most of it in the audited runs.

# The Bend model of `knot-vm-1`

`vm/model.bend` is the normative semantics of [SPEC.md](SPEC.md), written in
the I-profile from the spec text alone (no WAT exists on this branch). One
idea carries it: **the machine is a word store at SPEC addresses plus a few
registers, and every transition is a store update.** Cells, Activations and
the constant pool live in one store keyed by word address; the image is a
second, read-only store; frames are typed records whose word sizes match
§6's `[value[n], node, aux, head]` layout.

| Part | What it fixes |
|---|---|
| word store | a most-significant-first trie; absent words read 0 |
| codec | little-endian packing, strict UTF-8, the §2 decoder, the §2 encoder |
| validator | §4 rules 1-5, refusing in `serializer.py`'s order and wording |
| memory | §5 words and cells, power-of-two classes, LIFO free lists, bump allocation at the §5 heap base, uniform RC, the iterative release worklist bounded by the frame region, immortal constants, the terminal continuation |
| machine | §6's Eval/Return/Enter table, tail entry, inspection, Case selection, §7 fuel and quantum, §8 Book describe and Program phases, §9 prims, IO.print Actions |
| audit | `balanced` (rc equals owners among roots and edges; no word above an Activation's depth) and `leaked` (mortal cells still live) |

## Commands

```sh
S=scripts/bend-reference
$S vm/model-cli.bend -o .local/vm-model/model      # IMAGE FN FUEL [ORDINALS...] | IMAGE FUEL -- [ARGS...]
$S vm/model-audit.bend -o .local/vm-model/audit    # same arguments; RC audit before every transition, and calls
$S vm/model-sweep.bend -o .local/vm-model/sweep    # IMAGE FUEL; soundness of every single-word mutation
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

[LAWS.bend](LAWS.bend) states 23 laws, proved by [PROOF.bend](PROOF.bend):
- the codec round trip, on a hand-written plan and on five golden images;
- four refusal reasons, and bounded validator soundness: every single-word
  mutation of `value-on`'s function, constant and node sections is refused or
  runs soundly;
- symbolic machine equations over arbitrary states: an entry at fuel 0 is
  Exhausted, a finished machine is final, tail position, the Nat bounds, `x/0`,
  `x%0` and shifts by 32 or more;
- one audited run per fixture image (a Book per node family and a Program): its
  answer, the RC audit at every transition and zero live mortal cells after it.

These are bounded computed equations, not a refinement proof. The gate
evaluates the same predicates natively on more images: the audit on every
golden and the soundness sweep over every single-word mutation (zero,
successor, predecessor) of every golden, diffed against `serializer.py`.

## Known limits and deltas

- Effects: only `IO.print` is modelled. Applying any other foreign Action is
  `Unsupported vm foreign N`; vm-io adds the pure World.
- Inspection reads every operand word of a prim at its pinned type, including
  `String.append`'s moved tail, whose cells it does not traverse.
- A Nat renders as one visit; its unary text counts against the 16 MiB bound
  before it is built.
- A Nat Case allocates the predecessor's Big cell only when a Branch binds it,
  so a default arm leaks nothing (§6.1 does not say when).
- A refused transition leaves the machine as it was: the model's steps are
  atomic, including one refused mid-way by an allocation. An Enter's debit
  stands once paid (§7): a target that then stops the machine, such as D20's
  refused print, leaves its fuel and call spent.
- A stopped machine keeps the control it could not advance, so the words of a
  pending Enter stay owned (§7).
- The frozen eval suites have no images until the `image` encoder exists; the
  model's differential covers the 91 goldens and vm-spec's 17 admitted controls
  (three plan, seven code-list and seven run controls), each against the
  reference evaluation's outcome and call count (`vm/evaluate.py`).
- Deep lists recurse without a tail call (`pack`, `slice`); compiler-sized
  images are unmeasured. The checker's evaluator is slow: PROOF.bend takes
  about 100 s, most of it in the five audited runs.

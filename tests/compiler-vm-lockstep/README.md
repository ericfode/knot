# vm-lockstep: the WAT VM against its Bend model

Increment `vm-lockstep` of [VM-DESIGN.md](../../docs/compiler-campaign/VM-DESIGN.md). [REPORT.md](REPORT.md)
records what it found; this file says how it works and how to re-merge `campaign/vm-spec`,
`campaign/vm-model` and `campaign/vm-core` after D23.

Gate `vm-lockstep` (`python3 tests/compiler-vm-lockstep/check.py`, about three minutes) writes
`receipts/lockstep.json`. Nothing under `vm/` changes but one new file, `vm/model-trace.bend`; the pinned
release `vm/vm.wasm` (`vm/build.json`) is never rebuilt or edited.

## One state line per transition, on both machines

```
step | control | act | fuel calls quantum | top | frames | bump | free | output | heap
```

| Field | Model (`vm/model-trace.bend`) | VM (`js/vm-trace.mjs`, over the test build) |
|---|---|---|
| control | `Eval`, `Return`, `Enter` or `Finished` | `mode` with `node`, `val`, or `tgt`/`tfn`/`ops`/`nops` read from memory |
| frames | the typed frame list, printed as `kind,node,aux,n,values` | the words `[value[n], node, aux, head]` from the frame region |
| heap | every word from the heap base to the bump pointer, from its word store | the same words from linear memory |
| output | the printed lines | the host's `print` calls, less a Book's own `Evaluated` line |

A Book's answer is described inside the transition that returns it to Top, as the VM does, so step counts
agree to the end. The VM side uses only `vm_boot`, `vm_step`, `vm_dump` and memory: the test build already
exports them, and `vm.wat` is untouched. A print window (`STRIDE FROM TO`, in both tracers) samples long runs.

## Two strengths

The VM does not reclaim (`vm/CORE.md` choice 1: rc stays 1, free lists stay empty); the model does
(SPEC section 5). `lockstep.py` therefore compares at one of two strengths, chosen per state:

- **layout**: the model has freed nothing and both bump pointers agree. Every heap word is equal, except each
  cell's rc, of which only immortality is compared. Addresses are identical.
- **graph**: after the model's first reclamation. The words held by the roots (control, `act`, frame values)
  are matched one to one, and each pair of cells they reach must have the same class, header, metadata,
  padding and (matched) edges. rc, free lists and unreachable memory are outside it. The constants and the
  terminal continuation lie below the load-time bump pointer, are immortal, and stay word for word equal in
  every state.

`exact` (identity of addresses, rc and free lists) is implemented and controlled but not applied to the VM
until vm-rc: `lockstep.compare(..., mode='exact')`.

## Halting transitions

The model's transitions are atomic; the VM's two halts are not. Two documented relations are accepted, each only
at the halts it names, counted in the receipt and frozen in `frozen.json` (see REPORT.md, findings 1 and 2).
Everything else at a halt (outcome, meters, output, the frames and heap reachable, and a fuel stop's pending
Enter) is compared as at any state.

## Commands

```sh
python3 tests/compiler-vm-lockstep/check.py                      # the gate
python3 tests/compiler-vm-lockstep/lockstep-cli.py IMAGE FN FUEL [ORDINALS...]   # one Book, first divergence
python3 tests/compiler-vm-lockstep/lockstep-cli.py IMAGE FUEL -- [ARGS...]       # one Program
python3 tests/compiler-vm-lockstep/lockstep-cli.py --wasm MUTANT.wasm IMAGE ...  # another build of vm.wat
BEND_NO_TELEMETRY=1 python3 tests/compiler-vm-lockstep/bench/run.py --repeat 5 --out results.json  # speed ratio
```

The CLI builds the model's trace entry and the VM's test build into `.local/vm-lockstep` on first use, and
prints `DIVERGENCE at transition N, in FIELD` with both machines' state around it.

## Layout

| Path | Role |
|---|---|
| `vm/model-trace.bend` | the model's side: state after every transition |
| `js/vm-trace.mjs` | the VM's side |
| `lockstep.py` | parser, the two strengths, the halting relations, the D23 classifier, drivers |
| `runs.py` | the runs, taken from the sets `vm/check-model.py` already enumerates |
| `check.py` | the gate |
| `frozen.json` | recorded expectations: the D23 classes, the relation counts, the fuel-stop and suite-lane counts |
| `fixtures/long.plans.json` | two long runs across the 65,536-entry quantum |
| `lockstep-cli.py` | one image, first-divergence report |
| `bench/` | frozen bump-sized variants of `vm/bench`, the runner and its results |

## Re-merging D23 (in flight on `campaign/vm-spec`)

D23 makes an IO request a value, performed only where the Program's Top loop receives it. Both machines here
perform at application (the eager reading), so they agree with each other, and a Program whose effect is not
on the spine is marked `pending-D23` by `lockstep.classify_effects` (none exists among the frozen runs). When
vm-model and vm-core follow D23, the touchpoints are:

1. `vm/model-trace.bend`: `pending_text`, `control_text` and `frame_text` match every constructor, so a new
   `Control` or `Frame` variant fails to compile there, which is the signal. Print it in the same fields.
2. `lockstep.py`: `EDGES` (a new cell class for a request, if D23 adds one), `effect_of` (the effect moves to
   the Top loop's phase), and the class-at-most-4 guard in `Heap.cell`.
3. `frozen.json`: the D23 classes and the counts of the halting relations and of fuel stops, which change with
   the fuel accounting at the Top loop. Regenerate `receipts/lockstep.json` with `npm run gates:refresh`.
4. `js/vm-trace.mjs`: `vm_dump`'s register list, if vm-core adds a register (read from `vm/harness.mjs`'s
   `REGISTERS`, which the tracer imports).

Regenerate receipts; never merge them by hand.

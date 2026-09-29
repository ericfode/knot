# vm-lockstep: report

Branch `campaign/vm-lockstep`, made from `campaign/vm-model` (`07e6db73`) with `campaign/vm-core` (`de086bbe`)
merged in `7926e233`. Three shared files conflicted (the gate registry, its self-test and `GATES.md`); the two
census receipts were regenerated with `npm run census`, never merged by hand. Neither `vm/vm.wat`, `vm/vm.wasm`
nor `vm/model/*.bend` changed: gate `vm-lockstep` asserts `vm/build.json`'s pins, so the release module reported
here is the one vm-core froze (sha256 `9c483def…817c`). How the harness works: [README.md](README.md).

## Result against the acceptance

| Criterion (VM-DESIGN, `vm-lockstep`) | Result |
|---|---|
| VM equals model on complete machine state after every transition, on all golden images | **Met**, at two strengths and with two named halting relations (below). 296 runs, 2,940 transitions, 3,196 states compared, no other divergence; 82 further refusals refused alike; two long runs sampled (14 and 16 states of 350,008 and 440,008 transitions) with every state around the quantum yield. |
| VM equals eval-cli on value for every frozen eval fixture, under the Exhausted-lane rule | **Met for every fixture that has an image**: 137 goldens and Book invocations, plus 60 programs and 143 calls of four repository suites lowered from the oracle's core display. **The rest of the frozen suites have no image** (no encoder until `image`) and count as neither agreement nor disagreement. |
| Bench ratio at most 4× seed-native on each frozen workload, on a quiet host | **Not met, and above the 10× line for three workloads: stop for design review.** The host was loaded, and only one frozen source fits a bump arena. Numbers and blockers below. |
| A registered gate with mutants it kills | **Met.** `vm-lockstep`; 19 mutants (13 of the VM, 6 of the model) each killed at a named state through a wrong observation; 8 weakened comparisons each shown to let a mutant through. |

`BEND_NO_TELEMETRY=1 python3 tests/compiler-vm-lockstep/check.py` takes about three minutes standing alone.

## Findings for the owners

1. **The VM's halts are not atomic; the model's are (SPEC §6).** SPEC §6 says an ill-typed word halts "before the step
   changes any state". The model follows that. The VM pops a Gather frame before it inspects the operands or tests
   Succ's `NatRange`: CORE.md choice 8 records this for an ill-typed operand and calls it a stated limit no control
   observes. The NatRange stop has the same mechanism and is not named there. 23 of the 296 runs hit it. The lockstep accepts
   exactly this relation (model frames minus the top Gather equal the VM's, `top` less `n + 3`), only at
   `HostFailure image ill-typed` and `Exhausted 2 NatRange`.
2. **SPEC §6 disagrees with itself at Return to Top.** Its transition table drops `act` first ("Drop `act` and set it to
   0; then §8"), and §8's phase 3 then refuses an ill-typed IO.OP; the sentence above says such a refusal changes no state.
   The VM follows the table, the model the sentence. Two runs hit it (`inspect-halt-code`, `inspect-halt-message`). CORE.md
   does not record it. **Both findings need one normative reading**; the lockstep will follow it, and the relations in
   `lockstep.py` and their frozen counts (`frozen.json`) go away when a machine stops deviating.
3. **The zero-fuel reading is settled by evidence.** CORE.md called choice 8's zero-fuel state "a real ambiguity". At a fuel
   stop the VM keeps the pending Enter in `tgt`, `tfn`, `ops` and `nops`, and 95 fuel stops (89 goldens at fuel 0 and six
   fuel controls) match the model's `Stopped` control, target and operand words alike. Nothing more is needed there.
4. **The VM does not reclaim; the model does.** CORE.md choice 1: rc stays 1, `$dup` and `$drop` are empty. The model
   frees main's Activation at its first tail entry (`recursion-map`, transition 13), and every address after differs.
   Comparing raw memory would fail there for a reason SPEC §5 already explains. So the lockstep compares reclaim-blind (below),
   and `exact` strength (addresses, rc, free lists) waits for vm-rc. It is implemented and controlled now.
5. **Nothing else diverges.** No transition of any run differs in control, meters, frames, output or a cell the roots reach.

## What is compared

One line per state on both machines (`vm/model-trace.bend`, `js/vm-trace.mjs`): control, `act`, fuel, calls, quantum,
`top`, every frame, the bump pointer, the free lists, the output, and every heap word.

- **layout** strength while the model has freed nothing and the bump pointers agree (1,577 states): every word equal but
  each cell's rc, where only immortality is compared. Addresses are identical.
- **graph** strength once the model has reclaimed (1,619 states): a bijection built from the roots (control words, `act`,
  frame values), each pair of cells reached having the same class, header, metadata, padding and matched edges. rc, free lists
  and memory no root reaches are outside it.
- The constants and the terminal continuation, below the load-time bump pointer and immortal, are compared word for word
  at every state, whatever the strength.
- A model that has allocated more than the VM is refused.
- Not compared: rc words, free lists, and dead memory, until vm-rc; a Program's phase-3 relation above; the frames of a halt
  the VM has half done (relation 1); the pending control of any stop but fuel (the VM's registers cannot name it).

Comparator controls corrupt one field of a VM state and require the comparison to name it: control node and kind, `act`,
fuel, calls, quantum, `top`, a frame's `aux`, output, a mortal cell at layout strength, an Activation's owner word and a constant
at graph strength, and the halting outcome (13 controls).

**Long runs** are sampled (a state every 60,000 transitions, and every state within three of the yield at transition 327,675
and 367,675), so the every-transition claim holds for the 296 short runs, not for those two.

### Mutants

Each mutant is killed by a divergence at a named state, never by a crash or timeout: a side that produced no trace is counted apart
(`harness_faults`) and never as a kill. `state-only` means no run's final control or output changes; it does not mean no other
gate could see the bug (vm-core's frozen call counts and yields would likely catch the meters).

| Mutant | Machine | Breaks | Killed in | State-only | Runs | First kill |
|---|---|---|---|---|---:|---|
| `scope-slots-not-zeroed` | VM | a Scope pop leaves its slots' words in the Activation | heap | yes | 20 | `run:u32-file-alias` @6 |
| `call-frame-node` | VM | a Call frame's node word holds 7 | frames | yes | 78 | `model:char-match` @6 |
| `act-not-cleared` | VM | Return to Top leaves `act` at the released Activation | act | yes | 134 | `limit:arity-at-limit` @3 |
| `calls-counted-twice` | VM | each entry adds two to `calls` | calls | yes | 165 | `codes:lone-surrogate` @1 |
| `quantum-counted-twice` | VM | each entry adds two to the quantum | quantum | yes | 165 | `codes:lone-surrogate` @1 |
| `fuel-stop-drops-operands` | VM | a fuel stop forgets its pending Enter's operands | outcome | yes | 4 | `run:fuel-action-short` @12 |
| `fuel-charged-twice` | VM | each entry takes two fuel | fuel | no | 165 | `codes:lone-surrogate` @1 |
| `closure-entry-free` | VM | entering a Closure costs nothing | fuel | no | 18 | `run:inspect-halt-code` @4 |
| `describe-tag-off` | VM | a Book's printed tag is one too many | outcome | no | 104 | `limit:arity-at-limit` @3 |
| `arm-mirrored` | VM | a tag Case takes the mirrored row | control | no | 19 | `invoke-args:real` @2 |
| `reference-slot-below` | VM | Eval Reference reads the slot below | control | no | 133 | `argument:book-long-zeros` @3 |
| `activation-depth-off` | VM | an Activation starts one slot deep | heap | no | 165 | `codes:lone-surrogate` @1 |
| `gather-count-stale` | VM | a Gather counts its operands from one | frames | no | 91 | `codes:lone-surrogate` @2 |
| `scope-pop-off-by-one` | model | a popped Scope takes two words off `top` | top | yes | 20 | `run:u32-file-alias` @6 |
| `reuse-keeps-padding` | model | a reused cell keeps its padding's stale words | heap | yes | 11 | `closure-id` @13 |
| `quantum-never-resets` | model | the quantum counts past 65,536 | quantum | yes | 0 short, the long run | `loop-tail` @327,675 |
| `output-oldest-first` | model | a printed line joins the output at the wrong end | out | no | 2 | `non-scalar-unprinted` @65 |
| `bind-slot-off-by-one` | model | a Let binds one slot above its depth | heap | no | 10 | `run:nat-default-big` @4 |
| `call-frame-caller-lost` | model | a Call frame keeps no caller | frames | no | 78 | `model:char-match` @6 |

The three state-only VM mutants of the frame and heap (`scope-slots-not-zeroed`, `call-frame-node`, `act-not-cleared`) also pass
vm-core's own structural audit of `harness.mjs` after every transition of all 93 goldens (1,806 audited states, none broken), so
only the lockstep sees them. The model mutants `scope-pop-off-by-one` and `reuse-keeps-padding` are model bugs no output-level
observation shows: the first changes only the words the frames occupy, the second only the padding of a reused cell.

**Weakened comparisons.** Each of eight dimensions is dropped in turn (`calls`, `act`, `quantum`, `frames`, `heap`, `outcome`, `top`, `out`) and
one mutant that only that dimension sees must then survive; with the dimension on it is killed. So no dimension is idle.

**Exact strength** is controlled: an rc-only change of a mortal cell and a free-list-head-only change are passed by `auto` and refused by
`exact`, and the model equals itself in `exact` over 218 states. Against the VM `exact` fails on 86 of the goldens where the model first
frees a cell (`recursion-map`, transition 13); vm-rc turns it on for the VM.

## Value differential

The release `vm.wasm` through `scripts/run-wasm-io.mjs`, against vm-expected and, **live**, against the pinned eval-cli (literals `2ea222e`,
closures `a1d68911`, built natively). Every fixture is in exactly one bucket of the Exhausted-lane rule (SPEC §11):

| Bucket | Fixtures |
|---|---:|
| the VM equals eval-cli (value) | 82 |
| the VM refuses as eval-cli does (an invocation refusal) | 34 |
| eval-cli exhausted a documented bound (unary Nat, `Exhausted primitive budget`); the VM returns the seed's value | 3 |
| the seed succeeds beyond a VM bound; the VM stops `Exhausted` (bounds.json) | 3 |
| eval-cli unavailable (`Invalid parse function-result` on `IO(Unit)`); the VM shows the seed value | 4 |
| declared divergence by contract (D20's non-scalar output, `opaque-parameter`, `erased-field`, the describe domain) | 11 |

That is the 93 goldens and their 44 Book invocations. A golden's frozen eval-cli observation is re-executed too and must not have drifted.

**Frozen repository suites.** There is no encoder yet (`image`), so an image exists only where vm-spec's own method works: the oracle check-cli's
canonical core display lowered by `check-spec.from_display` over the program's own datatypes. On that path:

| Suite | Fixtures | Lowered, and the VM, live eval-cli and the frozen expectation agree | Calls | Rejected by the checker (a diagnostic is frozen) | Not lowered |
|---|---:|---:|---:|---:|---|
| `wasm` (seed tags) | 25 | 25 | 90 | 0 | none |
| `fields-wasm` (seed tags) | 8 | 6 | 24 | 0 | 2: an all-erased constructor (`erased`); the oracle exhausts its parse budget (`deep-call`) |
| `recursion` (Knot's eval line) | 19 | 11 | 11 | 8 | none |
| `fields` (Knot's eval line) | 40 | 18 | 18 | 21 | 1: an all-erased constructor (`all-erased-return`) |

The all-erased constructor is SPEC §8's declared image loss (`erased-field`). **The other suites (`baseslice`, `closures`, `generics`, `literals`, `checker`,
`catalog`, `frontend`: 241 fixtures) have no image**: their programs use Base types, closures or generics the lowering here does not
lay out, or they freeze no evaluation. Their rows in the receipt say so. None counts as agreement.

## Speed: first ratio

**Result: the ≤ 4× target is not met, and three of four measurable workloads are far above the 10× line that stops the increment for design review.**
It is a measurement, not a gate, and it is not a clean one.

Blockers, all recorded in `vm/bench/README.md` ("The workloads need reclamation") and confirmed:

- **No reclamation.** peano, list-fold and deep-recursion allocate 6 to 16 GB in a bump arena (4 GiB, D19). They ran only as smaller variants.
- **No encoder.** Every plan is hand-lowered from the frozen source and checked by its `True{}` guard only. `string-scan`'s `Bool.pick` is a function
  `hit`; `list-fold`'s Base `List<&2,U32>` is a user List (the workload's `workloads.py` says so).
- **No prims 39 and 40**: `sha256-64k` cannot run (`vm-prims`). `cps-choose` needs closure churn over the generic `choose`, not lowered here.
- **The host was loaded**: one-minute load average 22 to 28 on 18 logical CPUs (Apple M5 Max) during the measurement, 18 to 22 before it. It was never quiet
  in this session.

Method: `bench/run.py`. Every source, image and guard is frozen in `bench/workloads.json` before any timing (D7); the seed builds each variant with the
pinned native lane; both lanes run every workload alternately, seven times, as whole processes under `/usr/bin/time -l`, "subtracting neither lane's
start-up" as `vm/bench/README.md` says, and a null program is measured for each lane's start-up. The VM is the pinned release module.
`user + sys` is read to 10 ms, which does not resolve a seed run under about 50 ms, so cycles carry those rows.

| Workload (size) | Seed CPU s | VM CPU s | CPU ratio | Cycles ratio | Cycles ratio, start-up subtracted | Seed cycles per unit (frozen size) | VM cycles per unit | VM to seed per unit | VM peak RSS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `deep-recursion-b` (30 M levels; frozen 1 G) | 0.01 | 3.43 | 343 | 258 | 298 | 1.5 | 482 | **315×** | 1.84 GiB |
| `peano-b` (12 M product cells; frozen 200 M) | 0.02 | 2.56 | 128 | 82 | 87 | 10.2 | 891 | **87×** | 1.48 GiB |
| `list-fold-b` (12 M cells; frozen 240 M) | 0.02 | 3.49 | 175 | 151 | 164 | 7.1 | 1,208 | **170×** | 1.92 GiB |
| `string-scan` (9 M characters, **the frozen source, unchanged**) | 0.62 | 5.66 | 9.1 | 9.0 | 9.0 | 224.7 | 2,669 | **11.9×** | 1.92 GiB |

"Per unit" divides start-up-subtracted cycles by the work (levels, cells, characters), and sets the VM against the seed's median at the frozen size, so a variant's
short seed run cannot distort it. `string-scan` is the one workload measured at its frozen size on both lanes: the seed's 0.62 s is above the frozen 0.47 s
(measured under a lighter load), and the VM's 5.66 s is 9× that. Its VM cost is about 2,700 cycles per character; building one character makes six calls (each an Activation) and one list cell.

What the numbers mean: an entry-bound loop costs the VM about 240 cycles per entry (`depth` makes two entries per level, 482 cycles per level), against 1.5 cycles
per level for the seed at the frozen size. The escalation VM-DESIGN already ordered (dense tables and superinstructions, then a compact image, then
encode-time moves) is the design review this needs; The VM's bump
arena pays first-touch page faults a reclaiming VM would not (system time is 0.2 s of 3.4 to 5.7 s), and vm-rc adds rc work to every dup and drop, so
this RC-less ratio is not expected to improve by reclamation alone.

Timings are in `bench/results.json`; nothing gates on them.

## D23

Both machines perform an IO effect at application (the eager reading), so they agree with each other, and eager and D23 give one trace exactly when
every application of an Action to a continuation has only Scope and Call frames between it and Top (`lockstep.classify_effects`). The eight Program
goldens are all `spine` with the effect counts frozen by literal review (`frozen.json`: 1, 2, 1, 2, 1, 1, 1, 2), and six further controls are `spine`; **no frozen run is
pending-D23**, so nothing here changes when D23 lands beyond the touchpoints in [README.md](README.md). An effect under a Book (D22) or one that another frame
would drop or inspect is classified `pending-D23` and counted apart.

## What this does not claim

- Live Perch semantic and style review of `vm/model-trace.bend` and the lockstep sources is **pending**: no provider call was made (the increment's rule). Its
  offline preflight is the census and `npm run gates`.
- Not every transition of the two long runs is compared (14 and 16 states, and every state around the quantum yield).
- `state-only` describes final control and output only; a mutant may be killed by another gate.
- Only `IO.print` runs on either machine (vm-io owns the rest); the reference evaluation and both machines refuse other foreign leaves.
- The suites' images are lowered by vm-spec's own display method, which the checker's display and a hand-written plan cross-check on the goldens;
  a lowering defect would show as a disagreement, not hide one, but the lowering is not the encoder.
- The `bench/` framework's VM lane (VM-DESIGN's in-flight note) waits for `image`.

## Reproduce

```sh
export BEND_NO_TELEMETRY=1
python3 tests/compiler-vm-lockstep/check.py                                   # the gate
python3 tests/compiler-vm-lockstep/lockstep-cli.py vm/golden/recursion-map.kimg main 1000000
python3 tests/compiler-vm-lockstep/bench/run.py --repeat 7 --out /tmp/results.json
```

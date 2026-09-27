# Symbols bounded law review packet

Scope: the seven supported Table operations below. Helpers and constructors are
module-visible because Bend lacks export hiding; clients must not manufacture
InternTable or mutate its Vec/Trie fields. No delete/reset/reuse/generation/clone
API is promised. Pure state is affine and explicitly returned after each call.

## Contract and implementation summary

`new()->Table`, `bounded(U32)->Table`, `length(Table)->Table&U32`,
`limit(Table)->Table&U32`, `find(Table,String)->Table&Maybe<U32>`,
`intern(Table,String)->Table&Result<Error,U32>`,
`resolve(Table,U32)->Table&Result<Error,String>`.
Error is InvalidId or Exhausted. Abstract state is a distinct ordered name list.
Names compare exactly, including empty/NUL/Unicode; no normalization or hashing.
IDs are append positions in first-successful-intern order. Reordering first
insertions can change cross-build IDs. Namespace identity is caller-managed:
one table per namespace with an external namespace tag, or an injective encoded
key. No canonical remapping or cross-build-ID stability is promised. IDs belong
to one owning table lineage, not globally.
Bounds clamp to 16,777,216, preventing U32 overflow. Foreign-table numeric IDs
are a caller error and cannot be detected by the unbranded U32 API. Host OOM is
outside typed resource failure. Dropping a table ends its lifetime.

Implementation: intern first calls Trie.get. Some(id) returns the original Vec
and reconstructed Trie with Done(id). None reads Vec.length then Vec.push.
A push failure returns the same Trie and unchanged Vec with Exhausted; only
successful push performs Trie.put(name,old_length). resolve delegates to checked
Vec.get and maps failure to InvalidId. find and metadata reads retain both stores.
Reverse order/content and forward entries must agree.

The forward character trie stores an optional Here{id,more} at each prefix root,
separating the terminal binding from every U32 character, including NUL. Its
character siblings are Fork{color,char,less,same,more} red-black trees; same
continues the suffix. Here never occurs on less/more edges. Trie.get of an empty
suffix at a Fork can therefore return None immediately. Trie.insert retains a
nonempty suffix on LT/GT and consumes one character on EQ; only the prefix root
or same descent can introduce Here. Rotations move each char and same subtree
together. Trie.put blackens the outer root through an optional Here, and each
same subtree is blackened independently. Sibling roots are black, red/red edges
are absent, black heights agree, and sibling character order is strict.

Independent model (`model.bend`) imports Base and the shared command/reply data
protocol only. It linearly searches an ordered list, appends only on absent names
with room, and indexes by structural list recursion. It uses neither Vec nor
Map nor the implementation. Abstraction: Vec names equal this list in order;
Trie contains exactly each name at its list index. Runtime traces compare every
reply, length, limit, and *all* reverse names after every operation. Error tags
are compared distinctly. Forward reads and repeated interns in the same traces
catch an implementation that preserves reverse storage while losing its map.

## Law statements and domain witnesses

Universal, normalized with arbitrary String variable and zero preconditions:

- `first(name)`: in a limit-1 table, [intern(name),resolve(0),length] observes
  [(Id(0),1,1,[name]),(Name(name),1,1,[name]),(Number(1),1,1,[name])].
- `zero_limit(name)`: in limit 0, [intern(name),find(name),resolve(0)] observes
  [(Full,0,0,[]),(Missing,0,0,[]),(Invalid,0,0,[])].
- `empty_find(name)`: limit-3 empty table find returns Missing with [] preserved.

String is inhabited by "", "a", "ab", "é", and the explicit
SCon{Chr{0},SNil{}}. These instantiate all three universal domains. First creates
a nonempty table and an actually valid ID; zero_limit includes an invalid ID.
No unsafe witnesses, axioms, holes, or contradictory assumptions are introduced.

Five concrete normalization laws (not universal refinement): repeat_preserves,
full_preserves, unicode_exact, default_limit, clamp_limit. The first three assert
complete public trace equivalence to the independent model on the following
inhabited traces. The last two assert explicit empty contents, bounds and errors.

- repeat, limit 4: intern "a", intern "ab", intern "a", find "ab", find
  "missing", resolve 0/1, length, limit. IDs are 0,1,0; final names ["a","ab"].
- full, limit 1: intern "a", intern "b", intern "a", find "b", resolve 0/1/
  0xffffffff, length, limit. Full insertion fails; repeat succeeds with 0;
  lookup "b" remains absent and reverse 0 remains exactly "a".
- unicode, limit 6: intern "", NUL, "é", "é", "🪢", "é", find decomposed
  spelling, resolve 0 through 5. Five distinct names receive 0 through 4; repeat
  returns 2; 5 fails. Prefix/terminator distinctions include empty versus NUL.
- new: length 0, limit 16,777,216, resolve 0xffffffff Invalid.
- bounded(0xffffffff): effective limit 16,777,216 with empty contents.

`PROOF.bend` fills every law with conversion evidence and is checked as a whole.
Universal first-insertion behavior is substantive but does not establish
universal arbitrary-history refinement, Trie balancing correctness, or Vec correctness.
The latter claim remains a runtime-tested refinement boundary.

## Public-operation coverage matrix

| Operation | Laws | Independent runtime partitions/composition |
| --- | --- | --- |
| new | default_limit | example and benchmark tables, empty/default metadata |
| bounded | zero_limit, first, clamp_limit | limits 0/1/2/3, full1, unicode6, growth65 |
| length | first, repeat, full, default | all snapshots after every operation; 65 inserts cross capacities |
| limit | zero_limit, first, clamp/default | limit unchanged in all snapshots, zero and U32 max request |
| find | empty_find, zero_limit, repeat/full/unicode | absent/present, prefix, exact Unicode; after success/failure/repeat |
| intern | first, zero_limit, repeat/full/unicode | new/repeated/distinct, full-table existing success, failed insertion preservation |
| resolve | first, zero_limit, full/unicode/default | exact values at every valid ID, length boundary, U32 max, old values after growth |

Runtime: native CPU and JS both return 1 for `conformance.bend`. Exhaustively
checks all 12^3 command sequences at limits 0,1,2,3: 6,912 traces with snapshots
of every prefix. Alphabet: intern/find of "", "a", "ab"; resolve 0,1,2,
0xffffffff; length; limit. Additional targeted traces include 65 insertions,
lookup of the oldest name and boundary IDs 31/32/64/65, Unicode, and limit zero.
This is bounded testing, not an all-String or all-history exhaustive result.
Maximum physical allocation and host OOM are not exercised. GPU is unvalidated.

## Adversarial sensitivity

The unchanged named case runs green before each mutation. Each mutated main
parses/type-checks in isolation, its runtime test builds, and the same assertion
returns 0 (normal exit). Eight current executions are recorded in receipts/working/mutations.json;
original published-release receipts/mutations.json is retained unchanged:

| Mutant | Concrete unchanged witness that rejects it |
| --- | --- |
| alias_ids: new result always 0 | repeat trace second distinct "ab" expects 1 |
| forget_forward: fresh Trie on successful insertion | repeat "a" after inserting "ab" expects old ID 0 |
| repeat_grows: append existing name | repeat trace length/content and ID must remain unchanged |
| reverse_wrong: return "wrong" | Unicode trace exact first reverse name is empty |
| wrap_invalid: force Vec index 0 | full trace resolve 1 must return Invalid |
| exhaustion_success: return Done(0) | full trace intern "b" must be Full |
| failure_forgets: clear Trie after failed push | full trace intern "a" must still succeed at 0 |
| wrong_error: InvalidId changed to Exhausted | full trace resolve 1 expects Invalid, not Full |

No syntax/type/harness failure is counted. No survivors in this selected set;
mutation selection is not a completeness proof. Two map-loss mutants motivated
the narrow symbols-bidirectional-preservation Perch rule. Clean, broken and
held-out controls cover lost mappings after exhaustion and successful append.
Hostile review candidate: a reverse-only implementation could satisfy lengths
and reverse checks while forgetting forward entries. Both targeted preservation
traces kill it. Constant reverse/ID implementations are also killed. Remaining
scope: no arbitrary-history inductive refinement proof, physical maximum stress,
GPU execution or branded cross-table-ID enforcement.

## Additional representation checks

The unchanged independent model also observes 1,268 operations on each native/JS
lane across mixed terminal/NUL/prefix trees, sorted/reversed names, valid scalar
boundaries, supplementary characters, and all three-child insertion permutations
with the terminal inserted before/after. Each operation compares its full public
snapshot. A further 208 raw-U32 Char operations pass natively. Baseline and candidate
JS both reject surrogate 55296 and max-U32 character probes; these are backend
diagnostics, not portable String-success tests. The failed initial cross-backend
fixture assumption and its correction remain in the search evidence.

A separate consuming Bend auditor checks black prefix roots, red/red exclusion,
equal black height, strict sibling order, and Here placement at prefix roots,
including every nested same subtree. Rotation-order traces and their prefixes,
NUL/Unicode/repeat boundaries, sorted/reversed siblings and shared prefixes pass.
The frozen assertion rejects omitted rotations, missing outer/nested/Here
blackening and reversed comparison as type-correct semantic failures. These
additive finite checks do not constitute a universal inductive balance proof.

## Performance and trust

The unchanged native workload builds 16 tables at each size 128/256/512, interns
all names again and resolves each ID, checking all IDs and exact text. Nine paired
workloads with 0/64/256 additional common-prefix code points return zero errors.
Three alternating trials including process startup give candidate/baseline median
ratios 0.244–0.568. At 512 names the new medians are 0.0160/0.0727/0.2492 seconds.
Raw timings and hashes remain in style-campaign/iterative-identity/qualification/prefix06/benchmark.json.

The extra sorted/reversed one-character benchmark exposes a tradeoff: at 2,048
names and 16 table lifetimes, three alternating measured trials after one recorded
warmup yield candidate/baseline ratios 1.61/1.54. The rejected unbalanced trie
costs 68.9/66.7 times baseline on the same measurements. The chosen balanced
implementation removes that quadratic shape. Its forward bound is
O(sum_i log(s_i+1) + L+1), conditional on the sibling invariant, for examined
prefixes with s_i distinct next characters. Measurements are shared-host CPU wall
times, not allocation instrumentation, a universal speedup, or a GPU claim.

Trust: pinned Bend 2.0.29 checker/conversion, termination and erasure; native/JS
compiler/runtime; Base U32/Nat/Char/String/Array primitives; Vec's interface
and implementation. Whole loaded Base has 42 foreign definitions and unsafe
Array.fork/Array.join. The package does not invoke either unsafe operation or
foreign IO in its core, model or laws; native array and arithmetic lowering still
belong to runtime trust. No user unsafe/proof axioms. Exact closure and whole-book
trust inventory: receipts/working/closure.json. Vec is pinned to verified release 0xd684886d10b431b9dce6c3b2d1ef1980.

Perch remains advisory. Current live source and bounded-packet receipts are
retained in style-campaign/iterative-identity/; the source review covers 76
checks across 19 declarations with no findings. Offline wiring verifies all nine
packet rules and the dedicated rule on three controls, without pretending its
synthetic probabilities are calibration. The style search retains its frozen v2
rubric and a separate current v3 review after the coordinator's policy transition.
No full-package style pass or new publication is claimed. All original independent
Bend inputs, assertions, accepted laws and benchmark workloads are byte-identical;
only mutation source anchors and output paths changed in gate orchestration.

<!-- SOURCE_HASHES -->

Reviewed Bend source SHA-256 (refreshed by scripts/gates.py):

```text
66fd1e504762313ef78a6c0983eeecf36d524d287cbb2eaf9e100e4304a5686f  LAWS.bend
4b7349189631d7a9d126ea38a527e017129f43472274158dc6b6481a8f6134be  PROOF.bend
a03673f2f176fa9a51ef748cb50a4d2709929e197998b08c6a669263cebc26b3  benchmark.bend
ddb31933b99d600ebd1cba79376e2abc9110e37c3f9923b8dd5755b488c1ea53  cases.bend
4c1d737ce4f6f16086831796bfdabd32ffd0a856cc2c4c4854074a493b851fc7  conformance.bend
b64f7bbe8173e5b284f041b395ff2c88c7edeb3b5fa2e096a5d17185a2e6fe92  example.bend
8e44e7b0b147ad90cee9c049d62d44d8ba14bcbf0b7b07bc45044c24d2eacbeb  main.bend
9c08e11a3aa5938b333b75e411853dcda4ba426fbfaa524baa444b3bbac02270  model.bend
89842e8685126eea5182215f85fdcca3b3668f55e118f159dd482c6a42811e52  observe.bend
b1966247f544c4f3c373b55fc785fbaaf8a987b04ac003af00ab15a97aac139d  protocol.bend
fa928e0a78b1b88de072393f4dac1563de2822dae1bc4f366fc90fa0bc56eba3  release.bend
```

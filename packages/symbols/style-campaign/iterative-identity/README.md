# Symbols: iterative memetic search

2026-09-26. **Implementation improvement adopted locally; unpublished.**
The user's instruction to keep iterating superseded the initial one-candidate /
one-retry limit. We tried 24 further source variants across continuations, owned
phases, dependent views, shared bindings, and tree representations. Some variants
change only rendering/vocabulary; they are counted as candidates, not as 24 new
algorithms. Failed checks and rejected designs remain evidence.

The selected `phase/06_prefix_root` is byte-identical to `../../main.bend`, SHA-256
`8e44e7b0b147ad90cee9c049d62d44d8ba14bcbf0b7b07bc45044c24d2eacbeb`.
The pinned Vec import, seven public operations, exact-name/ID contract, independent
model, observation machinery, eight accepted laws and all original Bend tests and
benchmark workloads remain unchanged. The published Symbols import remains
`0xf5507d46d06a1a8043dcb1a582194615`; nothing was published by this search.

## What changed and why

An owned character trie replaces Base.Map in the forward index. Each prefix may
hold `Here{id,more}` for end-of-string. Its remaining character siblings form a
red-black tree `Fork{color,char,less,same,more}`. `same` consumes one character;
`less` and `more` retain the suffix. The terminal binding sits outside rotations,
so empty and NUL stay distinct and an empty lookup at Fork returns None directly.

The earned motif is the same three-direction grammar in lookup and insertion:

```bend
LT: Trie.rejoin(child => Fork{color,pivot,child,same,more},Trie.get(less,SCon{Chr{char},tail}));
EQ: Trie.rejoin(child => Fork{color,pivot,less,child,more},Trie.get(same,tail));
GT: Trie.rejoin(child => Fork{color,pivot,less,same,child},Trie.get(more,SCon{Chr{char},tail}))
```

This mechanism performs real public find/intern work. The reverse Vec, append
failure behavior and first-successful-intern ID assignment are unchanged.
The original compiler-support common-prefix workloads are faster; the adversarial
single-character family is slower, with its cost retained below.

## Policy transition and precise style result

The preregistered v2 rubric stayed fixed throughout candidate generation and
review. It gave the selected `Trie.get` 69% conceptual, 74% Delight and 62% memetic
level-3/4 mass: all three meet the unchanged 60% target. Its context is untruncated.
The 62% memetic result has a small margin; this is advisory model evidence, not
human taste calibration or measured popularity. The initial main had no memetic
passes among its 15 declarations; changed declaration inventories differ.

During integration, the shared coordinator installed user-approved rubric v3 at
`4d856ca1327d756f02938e2d3bdaba792df1a3cb`. It adds Anticipation/Payoff and requires
Galaxy brain for critical functions. A separate current-policy run on the
byte-identical adopted source gives `Trie.get`:

| Required v3 axis | Target mass | Result |
| --- | ---: | --- |
| Galaxy brain, level 5 | 0% | below |
| Delight, levels 3/4 | 92% | meets |
| Memetic identity, levels 3/4 | 62% | meets |
| Anticipation, levels 3/4 | 64% | meets |
| Payoff, levels 3/4 | 79% | meets |

**Current memetic coverage is 1/23; complete v3 coverage is 0/23.** The lookup is
contract-critical; its classification is appropriate. No classification, target,
rubric, test expectation or comment was manipulated to obtain a pass. The new
rating is justified by the explicit policy transition, not an unchanged retry.
No complete package pass or completion of the coordinator's separate pilot is
claimed. [Transition](policy-transition.json), [v3 receipt](current-policy-v3.json.gz).

All reviews resolved to `jev-1.13.0`. Full distributions, concentration/confidence,
source/helper identities and unresolved references are retained. Function context
is bounded to 16 helpers, four callers, 12 files and 48,000 bytes. The selected
lookup has no truncation, but built-in/type references remain unresolved. Selected
v2 Trie/Table datatype contexts are truncated. Current v3 Error/Trie/Table
contexts are truncated, so their Anticipation/Payoff ratings are unavailable.
These are context limits, not invented zero scores.

### Every selected changed declaration under frozen v2

| Declaration | Conceptual | Delight | Memetic | Disposition |
| --- | ---: | ---: | ---: | --- |
| `Color` | 79% | 55% | 9% | attention |
| `Trie` | 65% | 78% | 57% | attention |
| `Trie.black` | 85% | 64% | 4% | attention |
| `Trie.balance` | 18% | 64% | 27% | attention |
| `Trie.rejoin` | 97% | 63% | 17% | attention |
| `Trie.get` | 69% | 74% | 62% | all three meet |
| `Trie.insert` | 59% | 78% | 54% | attention |
| `Trie.put` | 87% | 61% | 21% | attention |
| `Table` | 74% | 49% | 5% | attention |
| `Table.bounded` | 97% | 58% | 2% | attention |
| `Table.new` | 93% | 37% | 2% | attention |
| `metadata` | 83% | 40% | 4% | attention |
| `Table.length` | 83% | 27% | 3% | attention |
| `Table.limit` | 84% | 30% | 3% | attention |
| `found` | 88% | 46% | 2% | attention |
| `Table.find` | 83% | 44% | 33% | attention |
| `inserted` | 85% | 66% | 7% | attention |
| `append_name` | 88% | 49% | 10% | attention |
| `intern_found` | 80% | 63% | 18% | attention |
| `Table.intern` | 60% | 66% | 40% | attention |
| `resolved` | 53% | 41% | 1% | attention |
| `Table.resolve` | 76% | 35% | 5% | attention |

See [full selected receipt](candidates/phase/06_prefix_root/style.json.gz). Error
was unchanged and excluded from that candidate-targeted run; the current v3 run
includes all 23 parsed declarations.

## Search ledger

Candidate authors used requested GPT-6 Astra / max settings in three bounded
sidecars. The provider's resolved author model/internal reasoning is not exposed
by the collaboration tool. Each lane records hypotheses before review and exact
first compiler attempts, diagnostics and later source variants. The parent
integrated only the selected source. No original assertion/law was weakened.

| Candidate | Rated declarations | v2 all-three passes | Highest memetic target mass |
| --- | ---: | ---: | --- |
| `cps/v01_pair_continuations` | 2 | 0 | 23% (Table.intern) |
| `cps/v02_owned_edit` | 7 | 0 | 47% (Edit) |
| `cps/v03_success_continuations` | 4 | 0 | 35% (Table.intern) |
| `cps/v04_church_table` | 14 | 0 | 32% (Table.intern) |
| `cps/v05_church_consumers` | 14 | 0 | 32% (Table.intern) |
| `cps/v06_two_faced_owner` | 16 | 0 | 53% (Table) |
| `cps/v07_direct_patterns` | 3 | 0 | 8% (intern_found) |
| `cps/v08_two_faced_sum` | 15 | 0 | 31% (Table.join) |
| `cps/v09_named_transpose` | — | — | unrated |
| `lenses/bijection` | 8 | 0 | 42% (Table.cross) |
| `lenses/bijection-handlers` | 9 | 0 | 49% (Table.cross) |
| `lenses/mirrored` | 8 | 0 | 30% (Table.resolve) |
| `lenses/persistent-forward` | 4 | 0 | 16% (Table.intern) |
| `lenses/red-black` | 23 | 0 | 43% (Table.intern) |
| `lenses/red-black-constructors` | 21 | 0 | 39% (Table.intern) |
| `lenses/shared-binding` | 20 | 0 | 51% (Table.cross) |
| `lenses/typed-view` | 7 | 0 | 46% (Table.view) |
| `phase/01_owned_stages` | — | — | unrated |
| `phase/02_owned_intent` | 5 | 0 | 30% (Table.intern) |
| `phase/03_frontier` | 13 | 0 | 23% (Table.intern) |
| `phase/04_trie` | 19 | 2 | 70% (Trie.put) |
| `phase/05_balanced_trie` | 23 | 0 | 66% (Trie.get) |
| `phase/06_prefix_root` | 22 | 1 | 62% (Trie.get) |
| `phase/07_read_only` | 20 | 0 | 57% (Trie.insert) |

The [index](candidate-index.json.gz) links every source snapshot, hypothesis, raw
gate and complete style receipt. Large JSON files are losslessly gzip-compressed.
The initial two rejected compiler attempts remain in `../intern-identity-1/`.

- Generic continuations and query views often improved compression/Delight but
  did not clear memetic identity. Domain vocabulary alone was insufficient.
- Unbalanced `04_trie` first cleared all three axes for both get and put. It was
  rejected after sorted characters exposed a quadratic sibling chain.
- `05_balanced_trie` fixed that shape but its extra Letter layer left lookup's
  conceptual rating uncertain. Prefix-root terminals removed that layer in 06.
- `07_read_only` honestly made the scalar trie Data and removed read rebuilding;
  it passed behavior but lost the memetic pass. It is retained, not adopted.

## Independent acceptance evidence

`qualification/prefix06/` contains the common parent gate, with frozen input
hashes and the unchanged source snapshot. The canonical package gate was also
run after integration; fresh receipts are in `../../receipts/working/`.

- Complete PROOF: zero holes; three arbitrary-String conversion laws and five
  concrete normalization laws. No universal arbitrary-history refinement claim.
- Unchanged native and JS conformance: 6,912 exhaustive length-three traces plus
  targeted Unicode/NUL/prefix, repeat/full, invalid-ID, growth and bound cases.
  Both local proof-inclusive release consumers return 1.
- All eight original semantic mutants still type-check and are killed by the
  same named independent cases. Source anchors changed only to address Trie.
- Additive oracle tests: 1,268 fully observed valid-scalar operations on each
  backend, including three-child permutations with terminal inserted first/last;
  another 208 raw-U32 Char operations pass natively. JS rejects the raw surrogate
  and max-U32 probes identically for the baseline and candidates. Initial fixture
  assumptions/failures remain evidence; no candidate was rescued by altered tests.
- Independent structural audits check root blackening, red/red exclusion, equal
  black height, strict sibling order, and prefix-root-only Here. For selected 06,
  nine type-correct omitted-rotation/blackening/order controls fail semantically
  on both backends; eight corresponding controls validate rejected 05. Hand-built
  checker controls verify exact failure bits, including black-height/Here faults.
- Four sorted/reversed/shared-prefix shapes at sizes 1,2,3,16,64,256,1024,4096
  pass structural checks on both backends. Maximum sibling depths observed are
  1,2,2,5,7,9,11,13. This finite evidence does not prove universal balancing.
- Live semantic Perch: 76 source checks across 19 definitions and nine bounded
  law-packet checks, 20 complete provider requests/responses, no findings.
  Offline wiring remains separately identified as synthetic evidence.

[Independent review](independent-review.md), [oracle/performance summary](adversarial-summary.json),
[original validation sources and receipts](validation-evidence.json.gz),
[source Perch](semantic-source.json), [law Perch](semantic-law.json).
The validation bundle includes exact textual sources and receipt hashes; binaries
and duplicated independent input files are omitted. Original inputs are preserved
in `../intern-identity-1/inputs/`.

## Measured performance and accepted tradeoff

Pinned native CPU, three alternating paired trials including process startup,
16 complete table lifetimes per workload. Every ID and reverse string is checked
by the unchanged Bend benchmark. All nine workloads return zero errors.

| Names | Extra common prefix | Baseline seconds | Selected seconds | Selected / baseline |
| --- | ---: | ---: | ---: | ---: |
| 128 | 0 | 0.0102 | 0.0058 | 0.568 |
| 128 | 64 | 0.0566 | 0.0207 | 0.366 |
| 128 | 256 | 0.1973 | 0.0608 | 0.308 |
| 256 | 0 | 0.0202 | 0.0090 | 0.445 |
| 256 | 64 | 0.1378 | 0.0415 | 0.301 |
| 256 | 256 | 0.5156 | 0.1299 | 0.252 |
| 512 | 0 | 0.0442 | 0.0160 | 0.362 |
| 512 | 64 | 0.2821 | 0.0727 | 0.258 |
| 512 | 256 | 1.0234 | 0.2492 | 0.244 |

The separate sorted/reversed single-character family uses one recorded warmup,
then three alternating measured trials and 16 complete tables. At 2,048 names,
ascending times are 0.014255s baseline versus 0.022930s selected (1.61x); descending
0.014796s versus 0.022762s (1.54x). At 128/512 names ratios are 1.02–1.29x.
The rejected unbalanced trie takes 0.982454/0.986386s at 2,048 names, 68.9/66.7x
baseline. The selected variant removes that adverse shape.

Acceptance judgment: keep the balanced trie for its explicit prefix/terminal
invariant, verified behavior, real memetic identity and common-prefix gains,
while accepting the measured sorted-character cost. There was no frozen universal
latency cutoff; no new cutoff was invented after seeing these results. This is a
tradeoff, not a blanket performance pass. Timings are from a shared host and do
not measure allocations, arbitrary workloads, maximum capacity, host OOM or GPU.

## Reproduction and maintenance

```sh
python3 packages/symbols/scripts/gates.py
python3 packages/symbols/scripts/benchmark.py
python3 packages/symbols/style-campaign/iterative-identity/qualify.py behavior packages/symbols/main.bend fresh-label
```

Gate scripts now write `receipts/working/`, preserving published receipts. An
optional `SYMBOLS_RECEIPTS_DIR` chooses another package-relative output directory.
The standalone qualification driver preserves unique labels, all original input
snapshots, and the fixed Bend assertions. Current implementation documents and
mutation-driver anchors may change during integration; original copies remain
hashed. A rubric transition affects review provenance, not deterministic tests.

To replay the additive checks, use `restore-validation.py` to reconstruct the
archived source/receipt tree under the ignored original scratch paths. It refuses
to overwrite different bytes. Original driver commands are retained in the
receipts. For a fresh additive run, pass a unique run ID to the observation driver;
for a fresh structural run, copy the selected invariant snapshot and main into a
new ignored directory and use the archived invariant runner.

Future work should seek mechanisms that expose a real domain invariant, then
check the entire composition and adverse input shapes before judging success.
The current Galaxy-brain gap requires separate substantive research; ordinary
wrappers should not gain layers or slogans merely to look distinctive.

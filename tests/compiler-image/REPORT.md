# Increment `image`: report

Branch `campaign/image`, built on `campaign/vm-spec` `60e80693`. Review round 1 merged `campaign/vm-spec` `54b52a84` (round 14)
and then `main` `c853cc5a`, and fixed two findings (below). Increment row: VM-DESIGN.md `image`. Nothing was pushed or merged.

## What was built

| Piece | Where |
|---|---|
| Erasure (the exhaustive match over `C.Term`) and the encoder entry | [src/image.bend](../../src/image.bend) |
| The plan and the limits and words every part shares | [src/image-plan.bend](../../src/image-plan.bend) |
| Layout as words, and the chunk stream | [src/image-layout.bend](../../src/image-layout.bend) |
| The decoder | [src/image-decode.bend](../../src/image-decode.bend) |
| Round-trip laws, their proofs, the open general law and its review | [src/image-LAWS.bend](../../src/image-LAWS.bend), [src/image-PROOF.bend](../../src/image-PROOF.bend), [src/image-OPEN.bend](../../src/image-OPEN.bend), [LAW_REVIEW.md](LAW_REVIEW.md) |
| `--profile=knot-image-1`, chunked writer, budgets | [src/compile-cli.bend](../../src/compile-cli.bend) |
| Lexer offset cap 65,536 -> 4,194,304 (the profile's character ceiling) | [src/lex.bend](../../src/lex.bend) |
| Gate `image`, registered in the runner | [check.py](check.py), `scripts/gates/run.py`, `test_runner.py`, GATES.md |
| Frozen expectations (an explicit source list and the reference images), independent reference, synthetic book, witnesses | [expectations.json](expectations.json), [reference.py](reference.py), [freeze.py](freeze.py), [synthetic.py](synthetic.py), [witnesses/](witnesses/) |
| The pinned seed's verdict on every Invalid source, and the generator of programs | [seed-audit.json](seed-audit.json), [audit.py](audit.py), [fuzz.py](fuzz.py) |
| Codec test driver | [image-cli.bend](image-cli.bend), [render.py](render.py), [writes.c](writes.c), [writes.js](writes.js) |
| Contract and census | `src/CONTRACT.json` `knot_image`, `src/SPEC.md`, `tools/census/approved.json` and the five regenerated inventories |

**`erase_tokens` is a projection, not a rewrite.** The task's law `decode(encode(b)) = erase_tokens(b)` cannot
mean "the book with its tokens blanked": the image also drops quantity-0 parameters, fields, lets and
arguments, renumbers levels as frame slots, and forgets datatype kinds and Type/Data. So
`erase_tokens : C.Book -> Result<S.Error,Plan>` projects into `Plan`, the image's own record tree, and the law
is `decode(layout(erase_tokens(b))) = erase_tokens(b)` wherever encoding answers, written `I.recoded(n,b) == I.erase_tokens(n,b)`
under `I.encode(n,b) == Done(w)` (partial correctness: the unconditional statement is false, see review round 1).

The encoder is four files because the Perch compiler manifest bounds a review group at 48,000 bytes; the
first draft was one 77 KB file. The manifest gained five groups (plan, encoding, layout, decode, laws).

Design, in three steps:

1. **`erase_tokens`** (`lower`): one arm for each of the eight `C.Term` constructors and no wildcard, so a new
   constructor cannot compile until it is encoded or refused. It keeps a scope from level to (slot, type),
   filters operands by the callee's or constructor's quantities, gives a Let its body's type, takes a Case's
   scrutinee type from its binder, orders a Case's arms by tag, turns an all-erased constructor into a `Value`,
   and computes `slots` as the exact maximum depth.
2. **`layout`** writes the plan as words: names interned in first-use order, absolute node offsets (nodes are
   placed twice, to size the constants section that precedes them), the header's digest and offsets, and the
   size and record limits checked before any word exists, and a name that is not an identifier refused first
   (`Unsupported compile image-name`). The words are records; `pull` cuts them into chunks.
3. **`decode`** is linear: children are the newest entries of a stack, so each record takes the entries its
   offsets name. It covers all thirteen opcodes, both Case modes and the constants pool.

`compile-cli` finishes checking, erasure, layout and the size test before it opens the output, then writes
the chunks through a fuel-bounded loop that threads the file handle. The default profile's arguments, usage
text, budgets and behaviour are unchanged: 25 frozen module hashes verify it, and a wrong argument count
still answers with the old usage text.

## Review round 1

Two confirmed major findings, both fixed; the commit messages and the gate's receipt carry the evidence.

1. **The general round-trip law was false as stated.** `recoded == erase_tokens` at every fuel and book is refuted by the
   seed's kernel: `encode` gives layout the fuel that erasure has and layout needs more (`flag_book` at fuels 1 and 2,
   `mixed_book` at 13 to 18); layout refuses what erasure accepts past the limits of vm/SPEC section 4 and for a name
   that `decode` does not read. Each is now a closed law (`!=`) in `src/image-LAWS.bend`. The law is restated as partial
   correctness, as ruled, and stays required and open (D21): whenever `encode` answers, decoding its words gives
   `erase_tokens` at the same fuel (`src/image-OPEN.bend`, [LAW_REVIEW.md](LAW_REVIEW.md), the trust inventory in `src/SPEC.md`,
   `CONTRACT.json`). Names were a further class, so layout now refuses a name that is not an identifier
   (`P.spelled`, shared with `decode`): no checked book has one, and all 96 books stay byte-identical. The gate reads the open
   law as written and proves it at 17 fuels and books, and must fail to prove the first statement at each of the eight fuels of
   its windows, and a law with a wrong conclusion.
2. **The gate froze Knot's own verdicts through a live glob.** The source list is now explicit (690: the 681 and the nine
   goldens of vm-spec round 14); only the images of the 96 books `check-cli` accepts are frozen, unchanged; every other source is
   compared with a `check-cli` built in the same run (same exit and stderr, both lanes). The seed's verdict on the 100 Invalid
   rows (`audit.py`, `seed-audit.json`): 83 rejected, 17 accepted, recorded D4 gaps that the gate does not judge. A gap that
   closes or a fixture that a merge adds moves no expectation (`judge_controls`).

## Evidence

Freeze history (D7). Frozen before any Bend of the encoder existed (commit `1aca8df3`): 676 sources, `check-cli`'s
verdict on each, the reference image of each accepted book (91), the profile's contract, the padded-source case and
the synthetic book. Changed afterwards, and recorded in the commit messages: the profile's emitter depth, 4,096 to
1,048,576 (`62657beb`, after measuring that each source nesting level costs several steps of the encoder's fuel); the
five witness books (5 more accepted, 681 sources), whose reference images come from `reference.py`, not from the
encoder (`81f9077e`); in review round 1 the shape of the file: an explicit list of 690 sources, no verdict of
`check-cli`, an explicit list of the golden images, every accepted row and the contract unchanged. The boundary controls,
the codec driver and the laws were written with or after the encoder, from that contract. Run
`BEND_NO_TELEMETRY=1 python3 -B tests/compiler-image/check.py`:

| Claim | Independent lane | Result |
|---|---|---|
| Every listed book the checker accepts encodes to the right bytes | `reference.py`: declarations read from source text + the core `check-cli` displays + `check-spec.py` projection + `serializer.py` layout | 96 of 690 sources (91 suite fixtures plus 5 witnesses), byte-identical on the native and Bun lanes; `serializer.validate` empty and re-encoding canonical for each |
| The other books are not misreported | this run's own `check-cli` (built from the tree under test) | 594 sources answer with the same exit and stderr on both lanes, nothing written; 17 of them are recorded D4 gaps, not judged |
| The Invalid verdicts, against the pinned seed | `scripts/bend-reference PATH --check-only` (`audit.py`, `seed-audit.json`) | 100 Invalid sources: 83 rejected by the seed, 17 accepted (D4 gaps) |
| Golden sources the core can express | committed `.kimg` files and `vm/evaluate.py` against `vm-expected.json` | 19 byte-identical to their golden images; each run under the reference evaluation, `invoke-words`' invocations included |
| `decode(encode(b)) = erase_tokens(b)` on each book | Bend's `erase_tokens` printed by `image-cli plan`, against `serializer.decode` of the compiled image | all 96 accepted books: the two texts are equal on both lanes, and `image-cli roundtrip` (Bend's own decode of its own encoding against its own `erase_tokens`) prints `equal` on the native lane (on the Bun lane it overflows the machine stack for the deepest fixtures, the seed's documented bound) |
| The Bend codec on random plans | `fuzz.py` plans encoded by `serializer.py` | 300 random plans a run with all 13 node forms, both Case modes, defaults, constants of each kind and closures: the Bend decode prints the reference's plan and `recode` writes the same bytes (native, and Bun on 6); offline, seeds 0 to 20,299, all equal |
| The Bend decoder and re-encoder | `serializer.decode` rendered by `render.py` | 207 images (111 golden, 96 compiled): same plan text, and `recode` reproduces every byte, on both lanes; all thirteen opcodes, keys mode, defaults, closures, foreign and the constants pool have real witnesses |
| The same on generated programs | `fuzz.py`, `reference.py` | 300 seeded programs a run (289 accepted in the committed receipt), each accepted one byte-identical to the reference and `equal` under `roundtrip` (12 also on the Bun lane); offline, seeds 0 to 20,399: 19,636 of 20,400 accepted, all byte-identical, valid and canonical |
| Decoder refusals | crafted images | 13, each with its frozen reason (`magic`, `registry digest`, `total`, `length`, `section offset`, `child offset`, `function root`, `case key` twice, image size `Exhausted`, and three for names: `name length`, `name padding`, `Unsupported image-name` for a wide one) |
| Names | `image-cli named`, both lanes | an identifier is encoded; `é` and the empty name are `Unsupported compile image-name` (exit 3) before any word exists |
| Default profile unchanged | `enum-baseline.json` | 25 module hashes on both lanes; usage text and caps as before |
| Budgets and outputs | literal controls | 23: each maximum and its successor, the 67,190-character book (default profile `Exhausted lex`, image profile `Built` with the unpadded image), the 4,194,304-character ceiling and one past it, and untouched output after Invalid, Unsupported and Exhausted |
| Chunked path | a DYLD write shim (native), a Bun `fs.writeSync` preload | a 5,170,376-byte synthetic image (sha256 equal to the frozen one) reaches the file in 95 writes, the largest 55,108 bytes, on both lanes; a 9,043,376-byte image, 166 writes (LETS = 6, native only: Bun would need about 2 GB) reaches the file through the same chunks, so the output cap admits at least 8 MiB by observation; a 4,842,844-word book is `Exhausted compile budget` before the output opens, and `image-cli answers` shows erasure answering on it |
| A missing arm is a checker error | the seed's `--check-only` | deleting any of the eight `C.Term` arms fails with the seed's message `cases for core.<Form>` |
| Mutants | wrong observations | 21 mutants of `src/image*.bend`, each a type-correct edit with a named witness; each ends as the compiler's own outcome (exit 0 with other bytes, or a categorized failure), never a seed fail-stop or a signal; 15 are also refused by the laws |
| Laws | the seed's checker | 28 laws, `All terms check.`; the general law in `src/image-OPEN.bend` type-checks, is exactly one open claim, and is proved at 17 fuels and books by the gate (the first statement is refused at each of the eight fuels of its windows, and a wrong conclusion at 64) |
| Judging of the listed sources | nine controls on real rows | a frozen book, a gap that closes, a source that moves, a checker that regresses or fails, a drifted reference, a missing source, and a source the seed rejects that `check-cli` accepts |

The synthetic book is 538 KB of source: 250 functions, each with three affine 256-field lets and a final one, so
node offsets pass 2^20 words. Its plan is generated with the source and checked against the checker's core on a
3-function instance (a `check-cli` whose parser depth is raised, since the shipped 512 stops below a 256-field
constructor). Cost: 0.8 s and 96 MB peak on the native lane, 2.3 s wall under load; Bun 9 s and 962 MB.

## Limits and honest gaps

- **The general round-trip law is an open obligation (D21), in its partial-correctness form.** The 28 laws are ground: two
  hand-written books and an all-forms plan, quantified over every source position, type, tag and slot where the words are only
  moved, plus erasure laws over every token, level, type and depth, plus the counterexamples of the first statement. The statement
  over all books and fuels is a real `law` in `src/image-OPEN.bend`, which the gate requires to type-check, be exactly one open
  claim, and hold at 17 instances; it is reviewed in [LAW_REVIEW.md](LAW_REVIEW.md) and recorded in `src/SPEC.md`'s trust
  inventory. Its evidence is the table above, not a proof; it is true as stated (no counterexample is known).
- **A name is an identifier.** A valid UTF-8 name that is not ASCII is admitted by the reference codec and is `Unsupported
  compile image-name` here. Two functions of one name are refused by `serializer.validate` and not by the Bend codec; the checker
  never lets a book carry them.
- **`Unsupported compile image-term` is unreachable here.** This base's core has no term the image cannot
  express, so there is nothing to report; the exhaustive match is the D4 mechanism for the forms that arrive.
- **Decoding is structural.** Scope, type and arity rules stay with the VM validator and `serializer.validate`
  (run on every image written). The reference codec's new refusal `constructor count` (round 13: a type record whose count the
  constructor table cannot hold) is a refusal here too, with another reason (`constructor record`: the Bend decoder reads a type's
  constructors as it goes, where the reference sizes them first), and it allocates nothing from the count; no encoder output can
  meet it.
- **Constants and the representation table are empty on this base**, so no compiled book exercises them. They
  are exercised through the golden images and the random plans by the codec driver, not through the encoder.
- **The encoder depth budget** counts recursion steps of `lower` and `place`, several per source nesting level
  (a Case arm costs a step for each constructor before it). The profile's default and maximum are therefore
  1,048,576, not the default profile's 4,096.
- **lex.bend changed one constant.** `step`'s 65,536 offset cap moved to 4,194,304. The default profile's fuel
  (at most 65,536) stops the lexer first, so its behaviour and every frozen frontend assertion are unchanged;
  the frontend gate re-passed.
- **The write observation is macOS-specific** (DYLD interposition) for the native lane; the Bun lane's preload is
  portable. The gate needs clang to build the shim.
- **No live Perch call was made** (none was allowed). Offline preflight, `--manifest=docs/compiler-campaign/manifest.json` (what the
  `perch-context` gate holds): 22 groups, 0 structural blockers, 0 truncated declarations, every composition available
  (`image-plan` 8,557, `image-laws` 27,081 of 48,000 bytes; the `perch-context` gate passes on the final tree).
  `node scripts/perch-style.mjs --preflight` on the eight changed and related Bend files as one target reports 334 declarations
  (290 before) and 77 truncated contexts (62 before: the thirteen new laws and one driver function exceed the helper limit, as the
  older laws do), and no composition (128,481 of 48,000 bytes for the eight files together). `lint:verify`, the offline half, ran in the full gates. Style and semantic review of the changed files
  remain the coordinator's.
- `npm ci` was not run: `node_modules` already held the pinned install.

## Verification of the branch

`BEND_NO_TELEMETRY=1 npm run -s gates` on the committed tree `a231ff8d` (the last commit that changes code; the commits after it
change documentation only): exit 0, 22 gates passed in 13 minutes 15 seconds wall (four workers, under the campaign's shared
load). Per-gate results:

| Gate | Result |
|---|---|
| frontend | 14 fixtures, 4 mutants, 24 boundaries |
| checker | 49 fixtures, 7 mutants, 10 budgets |
| structural, structural-trust | 16 fixtures, 7 mutants; 2 entries, 0 holes |
| fields, fields-trust | 40 fixtures, 9 mutants, 36 budgets; 4 entries, 0 holes |
| wasm, wasm-trust | 25 fixtures, 7 mutants, 44 boundaries; 3 entries, 0 holes |
| owned-store, flat-store | 3,532 cases, 6 mutants; 3,534 instances, 9 mutants |
| recursion | 19 fixtures, 3 mutants |
| fields-wasm | 8 fixtures, 4 mutants, 30 boundaries |
| census | 37 files, 758 declarations, 41 classes |
| perch-context | 33 controls, 8 mutants |
| lint:verify | 168 tests, 8 law rules |
| bootstrap | 934 corpus files, 8 stages, 54 mutants |
| classification | 17 fixtures, 6 mutants |
| io-host, io-abi-2 | 20 fixtures, 6 mutants; 43 fixtures, 5 mutants |
| selfhost | 65 cases (2 passed, 63 blocked), 5 D4 gaps, 20 judge mutants |
| vm-spec | 111 fixtures, 284 mutants, 255 boundaries |
| `image` | 690 sources (96 encoded, 594 answering as a live `check-cli`, 17 recorded D4 gaps), 19 goldens, 207 codec images, 13 refusals, 25 default module hashes, 23 profile controls, a 5.2 MB and a 9 MB image in chunked writes, 8 exhaustiveness controls, 21 mutants, 28 laws |

Also on that tree: `npm run -s gates:verify` (20 tests OK), `npm run census:check` (current), and every PROOF entry prints
`All terms check.` (`PROOF`, `catalog-PROOF`, `check-PROOF`, `fields-PROOF`, `recursion-PROOF`, `runtime-PROOF`, `image-PROOF`). The
seed is `bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts`, every run sets `BEND_NO_TELEMETRY=1`, no `.env` was read and no
provider was called. An earlier run on `28af72b4` (before the plan fuzz and the window laws) also passed all 22 gates.

Receipt drift, not failure: 15 tracked receipts (the three trust inventories, frontend, checker, structural, fields, wasm,
fields-wasm, recursion, classification, selfhost, both bootstrap receipts and perch-context) are classified `semantic` because they
record hashes of `src/*.bend`, `SPEC.md` and `CONTRACT.json`, and of programs built from them; no fixture observation changed.
64 receipts are identical and 11 differ only in volatile fields. The image receipt is `volatile-only`: current. `gates:refresh`
regenerates the 15.

## What the merge-wave follow-up must add

Work goes in `erase_tokens` (`lower`), where each new `C.Term` constructor makes the seed refuse to compile
until it has an arm; `layout` and `decode` already carry every form.

1. **literals** (`Literal`, `Intrinsic`, `Default`): U32/Char `Value`s become `Literal` constants; Nat and String
   literals go in the pool (interned by kind and data in node order, which `layout` already does);
   `Intrinsic` takes its id from `vm/registry.json`; a U32 or Char Case becomes keys mode with strictly
   increasing keys, first match kept, and a required `Default`; the header's representation words name the
   pinned Base types; `unsupported` for any reachable non-prim body that destructures `U32{Word}`.
2. **closures** (`Closure`, `Invoke`): captures renamed to ascending enclosing-slot order, `live_argument`, exact
   closure `slots`, `site` numbering (already done by `layout`), arrow types (kinds 1 and 2) in the shape table.
3. **io** (`Foreign`): hash-pinned foreign ids from the registry, `IO(X)` result types, Program entry kind 1
   with `main : IO(Unit)`.
4. **generics**: positional `none` types (a node's type is `none` where the core gives it an erased abstract
   type), erased type parameters, the `Con{none, List}` shapes.
5. **modules / Base slice**: the Base types among `shapes`, so the header's twelve representation words are not
   `none`; the bundle is then several files, so `image_load` reads the root only and imports go through the
   modules loader's `inspect` (knot-io-2 `path_identity`).
6. **nest**: lower the pattern matrix to the dense Case tables `lower` already builds.
7. Extend `expectations.json` (the reference's `from_display` already handles literals, closures and keys) and
   the witnesses, rerun `tests/compiler-image/check.py`, and flip the goldens that become expressible from
   "unavailable" to byte-identical.
8. Discharge, or keep recorded, the open D21 obligation for the general round-trip law (the trust inventory in `src/SPEC.md`). A
   form that the merge wave adds must keep `encode(fuel,book) == Done(w) -> decode(w) == erase_tokens(fuel,book)`; the gate's
   instantiation and fuzz show a violation first. A source that `check-cli` newly accepts needs no re-freeze: the live reference judges
   it and the receipt lists it as `newly-accepted`; re-run `audit.py` when a merge changes an Invalid verdict.

Merge notes: `src/SPEC.md` gains the section `Trust inventory: open proof obligations`, with the heading and table columns of
`campaign/nest`'s, so a merge of nest is a union of rows. The census inventories and `tools/census/approved.json` are regenerated (`npm run census:approve`,
`npm run census`) and will conflict with other branches; regenerate them on main. Other gates' tracked receipts
record hashes of `src/*.bend`, so they show semantic drift until `gates:refresh` (no fixture observation changed).

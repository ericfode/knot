# Increment `image`: report

Branch `campaign/image`, built on `campaign/vm-spec` `60e80693` (the vm-spec tip; it must merge first).
Increment row: VM-DESIGN.md `image`. Nothing was pushed or merged.

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
| Frozen expectations, independent reference, synthetic book, witnesses | [expectations.json](expectations.json), [reference.py](reference.py), [synthetic.py](synthetic.py), [witnesses/](witnesses/) |
| Codec test driver | [image-cli.bend](image-cli.bend), [render.py](render.py), [writes.c](writes.c), [writes.js](writes.js) |
| Contract and census | `src/CONTRACT.json` `knot_image`, `src/SPEC.md`, `tools/census/approved.json` and the five regenerated inventories |

**`erase_tokens` is a projection, not a rewrite.** The task's law `decode(encode(b)) = erase_tokens(b)` cannot
mean "the book with its tokens blanked": the image also drops quantity-0 parameters, fields, lets and
arguments, renumbers levels as frame slots, and forgets datatype kinds and Type/Data. So
`erase_tokens : C.Book -> Result<S.Error,Plan>` projects into `Plan`, the image's own record tree, and the law
is `decode(layout(erase_tokens(b))) = erase_tokens(b)`, written `I.recoded(n,b) == I.erase_tokens(n,b)`.

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
   size and record limits checked before any word exists. The words are records; `pull` cuts them into chunks.
3. **`decode`** is linear: children are the newest entries of a stack, so each record takes the entries its
   offsets name. It covers all thirteen opcodes, both Case modes and the constants pool.

`compile-cli` finishes checking, erasure, layout and the size test before it opens the output, then writes
the chunks through a fuel-bounded loop that threads the file handle. The default profile's arguments, usage
text, budgets and behaviour are unchanged: 25 frozen module hashes verify it, and a wrong argument count
still answers with the old usage text.

## Evidence

Freeze history (D7). Frozen before any Bend of the encoder existed (commit `1aca8df3`): 676 sources, `check-cli`'s
verdict on each, the reference image of each accepted book (91), the profile's contract, the padded-source case and
the synthetic book. Changed afterwards, and recorded in the commit messages: the profile's emitter depth, 4,096 to
1,048,576 (`62657beb`, after measuring that each source nesting level costs several steps of the encoder's fuel); the
five witness books (5 more accepted, 681 sources), whose reference images come from `reference.py`, not from the
encoder (`81f9077e`). The boundary controls, the codec driver and the laws were written with or after the encoder,
from that contract. Run
`BEND_NO_TELEMETRY=1 python3 -B tests/compiler-image/check.py`:

| Claim | Independent lane | Result |
|---|---|---|
| Every frozen-suite book the checker accepts encodes to the right bytes | `reference.py`: declarations read from source text + the core `check-cli` displays + `check-spec.py` projection + `serializer.py` layout | 96 of 681 sources (91 suite fixtures plus 5 witnesses), byte-identical on the native and Bun lanes; `serializer.validate` empty and re-encoding canonical for each |
| The other books are not misreported | `check-cli` | 585 sources answer with the same exit and stderr, nothing written |
| Golden sources the core can express | committed `.kimg` files and `vm/evaluate.py` against `vm-expected.json` | 19 byte-identical to their golden images; each run under the reference evaluation, `invoke-words`' invocations included |
| `decode(encode(b)) = erase_tokens(b)` on each book | Bend's `erase_tokens` printed by `image-cli plan`, against `serializer.decode` of the compiled image | all 96 accepted books: the two texts are equal on both lanes, and `image-cli roundtrip` (Bend's own decode of its own encoding against its own `erase_tokens`) prints `equal` on the native lane (on the Bun lane it overflows the machine stack for the deepest fixtures, the seed's documented bound) |
| The Bend decoder and re-encoder | `serializer.decode` rendered by `render.py` | 198 images (102 golden, 96 compiled): same plan text, and `recode` reproduces every byte, on both lanes; all thirteen opcodes, keys mode, defaults, closures, foreign and the constants pool have real witnesses |
| Decoder refusals | crafted images | 10, each with its frozen reason (`magic`, `registry digest`, `total`, `length`, `section offset`, `child offset`, `function root`, `case key` twice, image size `Exhausted`) |
| Default profile unchanged | `enum-baseline.json` | 25 module hashes on both lanes; usage text and caps as before |
| Budgets and outputs | literal controls | 23: each maximum and its successor, the 67,190-character book (default profile `Exhausted lex`, image profile `Built` with the unpadded image), the 4,194,304-character ceiling and one past it, and untouched output after Invalid, Unsupported and Exhausted |
| Chunked path | a DYLD write shim (native), a Bun `fs.writeSync` preload | a 5,170,376-byte synthetic image (sha256 equal to the frozen one) reaches the file in 95 writes, the largest 55,108 bytes, on both lanes; a 9,043,376-byte image, 166 writes (LETS = 6, native only: Bun would need about 2 GB) reaches the file through the same chunks, so the output cap admits at least 8 MiB by observation; a 4,842,844-word book is `Exhausted compile budget` before the output opens |
| A missing arm is a checker error | the seed's `--check-only` | deleting any of the eight `C.Term` arms fails with the seed's message `cases for core.<Form>` |
| Mutants | wrong observations | 19 mutants of `src/image*.bend`, each a type-correct edit with a named witness; each ends as the compiler's own outcome (exit 0 with other bytes, or a categorized failure), never a seed fail-stop or a signal; 13 are also refused by the laws |
| Laws | the seed's checker | 15 laws, `All terms check.`; the general law in `src/image-OPEN.bend` type-checks and is exactly one open claim |

The synthetic book is 538 KB of source: 250 functions, each with three affine 256-field lets and a final one, so
node offsets pass 2^20 words. Its plan is generated with the source and checked against the checker's core on a
3-function instance (a `check-cli` whose parser depth is raised, since the shipped 512 stops below a 256-field
constructor). Cost: 0.8 s and 96 MB peak on the native lane, 2.3 s wall under load; Bun 9 s and 962 MB.

## Limits and honest gaps

- **The general round-trip law is an open obligation (D21).** The 15 laws are ground: two hand-written books
  and an all-forms plan, quantified over every source position, type, tag and slot where the words are only
  moved, plus erasure laws over every token, level, type and depth. The statement over all books is a real `law`
  in `src/image-OPEN.bend`, which the gate requires to type-check and be exactly one open claim, and it is
  reviewed in [LAW_REVIEW.md](LAW_REVIEW.md) and `src/SPEC.md`. Its evidence is the table above: per book, the
  observed equality on all 96 accepted books, not a proof.
- **`Unsupported compile image-term` is unreachable here.** This base's core has no term the image cannot
  express, so there is nothing to report; the exhaustive match is the D4 mechanism for the forms that arrive.
- **Decoding is structural.** Scope, type and arity rules stay with the VM validator and `serializer.validate`
  (run on every image written). Names are ASCII; a wider name is `Unsupported compile image-name`.
- **Constants and the representation table are empty on this base**, so no compiled book exercises them. They
  are exercised through the golden images by the codec driver, not through the encoder.
- **The encoder depth budget** counts recursion steps of `lower` and `place`, several per source nesting level
  (a Case arm costs a step for each constructor before it). The profile's default and maximum are therefore
  1,048,576, not the default profile's 4,096.
- **lex.bend changed one constant.** `step`'s 65,536 offset cap moved to 4,194,304. The default profile's fuel
  (at most 65,536) stops the lexer first, so its behaviour and every frozen frontend assertion are unchanged;
  the frontend gate re-passed.
- **The write observation is macOS-specific** (DYLD interposition) for the native lane; the Bun lane's preload is
  portable. The gate needs clang to build the shim.
- **No live Perch call was made** (none was allowed); `lint:verify`, the offline half, ran in the full gates.
  Style and semantic review of the four image files remain the coordinator's.
- `npm ci` was not run: `node_modules` already held the pinned install.

## Verification of the branch

`BEND_NO_TELEMETRY=1 npm run -s gates` on the committed tree (`ee4248dc`): exit 0, 22 gates passed in 250 s wall
(four workers, under the campaign's shared load): checker, structural, structural-trust, owned-store, fields,
fields-trust, frontend, flat-store, census, wasm, wasm-trust, lint:verify, perch-context, classification, recursion,
io-host, bootstrap, fields-wasm, io-abi-2, vm-spec, selfhost and `image` (681 sources, 96 encoded, 19 goldens,
198 codec images, 10 refusals, 25 default module hashes, 23 profile controls, a 5.2 MB and a 9 MB image in
chunked writes, 8 exhaustiveness controls, 19 mutants, 15 laws). The baseline on the vm-spec tip (`60e80693`)
passed its 21 gates the same way. The seed is `bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts`, every run sets
`BEND_NO_TELEMETRY=1`, no `.env` was read and no provider was called.

Receipt drift, not failure: fourteen tracked receipts (frontend, checker, structural, fields, wasm, fields-wasm,
recursion, classification, selfhost, bootstrap and the three trust inventories) are classified `semantic` because
they record hashes of `src/*.bend`, `SPEC.md` and `CONTRACT.json`, and of programs built from them; no fixture
observation changed. The bootstrap receipt also lists the four new source files in its corpus. `gates:refresh`
regenerates them; the image receipt is new and current.

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
8. Discharge, or keep recorded, the open D21 obligation for the general round-trip law.

Merge notes: the census inventories and `tools/census/approved.json` are regenerated (`npm run census:approve`,
`npm run census`) and will conflict with other branches; regenerate them on main. Other gates' tracked receipts
record hashes of `src/*.bend`, so they show semantic drift until `gates:refresh` (no fixture observation changed).

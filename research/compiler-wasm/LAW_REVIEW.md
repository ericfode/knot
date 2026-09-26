# Source-to-Wasm enum profile: bounded review packet

Scope: the first complete enum-profile pipeline, not full S1, self-hosting or GPU
source lowering. Bend source is lexed, parsed, resolved and checked by Knot;
`compile-cli.bend` emits a real Wasm file. `eval-cli.bend` independently evaluates
checked source terms. Both implementations are Bend 2. Python/Node drive builds,
files and execution only. The seed/reference pin is Bend 2.0.29 at
574b6d39a235b539eb19a5c532993a0abb3d11ad. No output-C parity is required or used.

## Contract, domain and abstraction

Accepted input: ASCII, LF/spaces/comments; no imports/Base; nonempty nullary
Type/Data enums; fully typed first-order functions; fixed erased/affine/reusable
quantities; calls, shadowing locals, exhaustive nonoverlapping parameter matches.
Every function is checked, including unused definitions. Constructor refinement,
parameter matching order and erased-context scope/type checks follow the pinned
seed. Fields, general recursion, dependent types, effects and overlaps remain
explicitly outside this first profile. It accepts Flag and more than constants.

`eval.invoke(book,name,args,fuel)` consumes a checked book and external live enum
ordinals. A Value is (type-id,tag). Environments map lexical levels to Values;
frames retain the caller environment for a local binding or remaining arguments.
Evaluate, Return, Arguments and HostArguments are explicit source-machine states.
One step costs one transition. Returning the terminal Value costs no further fuel.
Erased arguments/initializers are skipped before Evaluate, including forward erased
calls. Live arguments run in source order. A match selects the tagged checked arm.
Wrong external arity/range/export is HostFailure. An impossible checked-core shape
is InternalFailure. These reusable Value records model only pure nullary enums;
they are not a general runtime heap for affine resources.

`wasm.emit(book,depth,cap)` consumes a checked book and returns exact bytes or an
explicit failure. It does not import/call eval. It maps source lexical levels to
compact Wasm local indexes, omitting erased parameters/initializers/arguments.
Live arguments precede a direct call. A local initializer emits a local.set before
its body. Branches independently inherit the same local map and may reuse physical
slots; the enclosing declaration reserves the maximum of their needed slots.
Matches emit i32 equality plus typed if/else; the last arm is the exhaustive tail.
Correctness here presumes external argument ordinals belong to their declared enum.

The abstraction is: an evaluator Value(type-id,tag) corresponds to the i32 tag in
a Wasm parameter, local or result whose source type is known from the checked book.
Neither implementation may replace a whole function with its evaluated result.
Every source function is exported. Wasm version 1 sections are exactly 1/3/7/10;
instructions are i32.const, local.get/set, call, i32.eq, if/else/end. No imports,
memory, GC, SIMD, threads or WASI. The host is Node 22.22.3 on macOS arm64.

Byte fragments and section payloads use the published checked ByteOutput API,
0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend: fragment/compose enforce byte range
and capacity without wrapping length arithmetic; finish preserves byte order.
Unsigned LEB encodes section sizes/indexes. Signed positive LEB encodes enum tags
with a 6-bit last group; tag 64 must be [192,0], not [64] (which means -64).
Five groups cover U32; positive signed encoding rejects values above 2^31-1.
Actual enum tags are at most 255. Names are accepted ASCII identifiers.

The checked-core and helper constructors are not validated public package APIs.
Callers of emit/invoke must first call check; fabricated indexes, malformed arm
lists and out-of-range quantities do not satisfy that invariant. Source-level
catalog caps are 256 types/functions/constructors/parameters, 4,096 lexical levels.
Input defaults are 65,536 characters and 512 parser/checker depth. Emitter depth
is 4,096, output 65,536 bytes (maximum override 1,048,576). Eval accepts up to
1,048,576 transitions. Source-machine steps are a total budget; parser/checker/
emitter fuel is depth, while source/catalog caps bound structural list traversals.
No throughput, asymptotic optimization or arbitrary-host stack guarantee is made.

Semantic rejection or exhaustion finishes before output is opened. File writes
use pinned File.write_bytes. HostFailure can leave a partial file; absence of a
fresh Built record and successful exit prevents it counting as emission. Existing
files are not erased on semantic failure. Atomic replacement/crash durability is
not promised. The host test checks current bytes, not file presence alone.

## Evidence and public-operation coverage

`python3 tests/compiler-wasm/check.py` builds native and Bun compiler/evaluator
entries, checks the complete proof entry and executes actual modules on Node.
The literal manifest fixes inputs, expected tags, constructor names and upstream
call expressions independently of Knot output. Reference calls are small import
wrappers around each source fixture; qualification of printed names is explicit.

| Operation / contract | Evidence | Limits |
|---|---|---|
| source -> check -> emit -> file | 25 programs; native/Bun byte-identical modules; all decode/validate/instantiate/run | Finite profile corpus, no general lowering theorem |
| invoke / environments / frames / branch select | 90 upstream calls; same 90 evaluations per seed host; same Wasm results per module host | Domain-valid selected calls, not every tuple of the 129-parameter case |
| lexical->physical locals / argument order | shadowing, repeated parameter names, branch-local bindings, first/second with an erased middle arg, 129th live parameter | No closures or fields |
| erased ABI and execution | erased forwarding/binding/calls, mixed types, live arity checked by Node; erased-cost finishes at exactly 6 steps | No effects/affine resource cleanup |
| instruction and format contract | section IDs exactly 1,3,7,10; wasm2wat opcode inspection; Node validate/compile/instantiate | Decoder/engine and seed remain trusted |
| index/tag/length encodings | tag 63/64/127/128/255; call/index 128; 129 live parameters; section lengths >127; literal LEB laws | No universal LEB roundtrip proof |
| rejection boundary | 32 earlier Invalid/Unsupported cases through both compiler and evaluator on both hosts, no emitted module | Overlap Unsupported differs intentionally from seed acceptance |
| resource and host boundaries | 44 observations: each stage exhaustion, exact 68-byte output versus 67-byte failure, exact eval budgets, stale outputs, unsupported syntax, missing files, output directory, bad/huge budget, bad ordinal/arity/export | No simulated disk-full write or OS crash; write caveat stated |

The earlier parser/checker deterministic gates are rerun after the additive Host
error variant. Their four parser plus seven checker laws remain filled and their
literal trees/rejection observations and semantic mutants pass. The new proof
entry imports those complete entries rather than bypassing earlier obligations.

## New laws and inhabited witnesses

`runtime-PROOF.bend` fills four source-machine boundary/transition laws:
1. A terminal Return(value,[]) succeeds at zero remaining fuel (arbitrary value/book).
2. Pending Evaluate(term,env,frames) at zero fuel is Exhausted (arbitrary fields/book).
3. An erased Let steps directly to its body with the original environment/frames;
   its arbitrary initializer is not evaluated.
4. Returning through Bind(level,body,caller-env) evaluates body with precisely that
   value bound at that level in the retained caller environment.

Three further laws are **concrete codec normalization**, not universal roundtrips:
unsigned 128 = [128,1]; signed-positive 64 = [192,0]; unsigned U32 max =
[255,255,255,255,15]. Complete proof checking reports All terms check, zero holes.
Ordinary Enum values, lexical levels 0/1, empty/nonempty environments, Bind frames,
and literal byte lists inhabit every domain; no unsafe inhabitant/axiom is used.
The laws specify helper behavior. Whole-program agreement comes from independent
reference observations and real Wasm execution; it is not inferred from helper
proofs alone. There is no universal checker-soundness, compiler-refinement, or
source-machine-to-Wasm simulation theorem in this milestone.

## Mutation and hostile review

Seven parseable/type-correct Bend implementation mutants compile successfully:
- All emitted constants zero: valid Wasm returns the wrong Flag value.
- Equality changed to inequality in matching: valid Wasm chooses the wrong arm.
- All parameters mapped to local zero: valid Wasm second(Off,On) returns Off.
- Initializers stored into local zero: valid Wasm shadowing returns the wrong value.
- Signed LEB treated as unsigned: a valid module returns -64 for source tag 64,
  rejected by the host's result-domain check.
- Evaluator literals forced to tag zero: its normal result differs from fixed
  source/reference expectations.
- Evaluator executes an erased initializer: erased-cost incorrectly exhausts its
  defined six-transition budget. This is explicit machine exhaustion, not timeout.

All five emitter mutants produce binaries accepted by independent wasm2wat; the
host validates each before invoking it. Evaluator mutants run as ordinary compiled
Bend. The tests preserve literal expectations. A malformed/type-invalid mutant,
import failure or host timeout cannot count as a semantic kill. Exact mutation
selectors, source hashes and outputs are retained in the gate receipt.

Adversaries: a constant compiler fails both inputs of flip; name-only local lookup
fails shadowing; multiplying caller usage by reusable callee quantity would reject
Data promotion controls; dropping checks for unused/erased definitions misses
existing negatives. A byte-format bug can leave a file with a plausible name;
validation and execution inspect newly produced bytes after a successful process.
A reversed arm/argument mapping cannot hide behind all-main-On checks because
noncommutative first/second, three colors and direct export calls vary results.

## Trusted closure and remaining work

The seed-load inventory is `receipts/trust.json`: 14 compiler, 12 evaluator and 17
proof-entry Bend files, with exact hashes. Pinned Base has 42 foreign definitions
and two unsafe Array declarations in the checked closure. Executed foreign effects
are only IO.args, File.open/read/close, IO.print, and compiler File.write_bytes.
Primitive/native lowering, the seed checker, byte package and host engine remain
trusted. No published package source or GPU prototype changes in this increment.
Whole-runtime intrinsic correctness is not implied by the foreign inventory.

GPU source lowering, structural recursion/fields, full Base acceptance, compiler
self-hosting and useful performance are subsequent milestones. The actual WebGPU
prototype remains separate historical device evidence. No style ranking is claimed:
this increment contains complementary evaluator/emitter machines, not equivalent
alternative implementations suitable for a ranked comparison.

## Reviewed implementation hashes

- `src/LAWS.bend`: `5db3a525420e9cff3448b0a7219ff71b10a8dc111d6e440007c2a0ae7e8fa76d`
- `src/PROOF.bend`: `c0313e180f55d3941f6bae25a7c4d4362f883495bb54dcb570ef62825eb43a80`
- `src/catalog.bend`: `d734d9cd3f7b6d9599a6663d19e6a8114497e53fd01255139905dc8cb41ce762`
- `src/check-LAWS.bend`: `3d3cccaed0e131f1ed185472dfe63cc4208ab3dbbf51a72c419b52ff0d599fde`
- `src/check-PROOF.bend`: `2fe6bce9d7f4e03042794864e8249ffbd2e9b0d4824453f633b4483ac8bf0a9d`
- `src/check-cli.bend`: `7cbcc66c6586a1a5e5997a8b0771d791219d368a0ebaa1febffa07702c3e5705`
- `src/check.bend`: `55818425ddbd7cdac13bc08543336aaf21f6df5fefd5613649f4332b69035d13`
- `src/checked-display.bend`: `6f6184f62376d5b527405e4304e38ed989fff960a258b9909226126d48050c79`
- `src/compile-cli.bend`: `0dcf1a573669f4f2a73a73d1dec73063ad2ed7ba106313865f8eb5233f1fc079`
- `src/core.bend`: `c8341c310680b35e292e60fa2b1ab691e5ce0b07b26d695a07c03a652e8b4fc0`
- `src/diagnostic.bend`: `6d7b0b0052fcb1809449b0b6df3f26f2bbdac7ff3e68c7b292727068e4b350f6`
- `src/driver.bend`: `4c1b4d1fb9a412e1e9fda6474bde2bd3b0524774543d0d857fdd75bf5b548c9d`
- `src/eval-cli.bend`: `e98918b85bee9d62067405dafece47766fd5c890098b5b9131aae9e5537d91ee`
- `src/eval.bend`: `ba318e44c13355cd9731514615b2fa0a68d9c4087bbf3dbc847dea12d62bc7cc`
- `src/lex.bend`: `1e4668537a254764ecd5b0830511d7b9ee1a21e830d03ae7fea78a1d8578c4b3`
- `src/parse-cli.bend`: `7a4feaec7c67c3a8ed7909d46dbef4ca8f5897857b769976f9e2704e67400c90`
- `src/parse.bend`: `22cc65edc3ba1f50800426e1218c587a89e667a665b8779bdbb5a4ae7895a4ab`
- `src/runtime-LAWS.bend`: `7217b5155135ed541a111565134f1484993157a1a5c229130bedec3a3fff747a`
- `src/runtime-PROOF.bend`: `747f3fc497bb201d8c94e3e5a5367e24cfa9a56c7aaa73b59d451b35800b6874`
- `src/scope.bend`: `4657604c5c0a5cf7aa61729188a36016926c3ee8ff06d93c488cdfaaa834a4dd`
- `src/syntax.bend`: `ee53d8f943cd7d2fde831769997e12e923b1cf7b46b2e640812ce060d3ec3760`
- `src/wasm-bytes.bend`: `d828d6078ae84973ce2da7d3a5d47ccc7cceb6eeb3300319f142d25eec970aac`
- `src/wasm.bend`: `e03d155aab051e37e699cad23c313837cc1fdb89bec70d02bff5c391712586a6`
- `src/CONTRACT.json`: `3e345be4e44464a26fc7320f8fcc621b7de355f7d6fa5a2ba82ab65395eefa30`
- `scripts/run-wasm.mjs`: `6f305fae310364a106580900ff645eebd7bf021473ecabba73de6dabc99239d5`
- `tests/compiler-wasm/check.py`: `77c2197f98e827b97758138cc934ffab665b908f608dfefd32ef7d2ee138b28d`

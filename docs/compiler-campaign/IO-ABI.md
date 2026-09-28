# Knot IO ABI: `knot-io-1`

This is milestone 10's **host boundary**, qualified independently of Knot
lowering. Under D14 the Wasm VM imports this ABI to execute serialized Knot
images. The ABI has no dependency on image, heap, closure or native Wasm
lowering layouts. The frozen authority is
[`tests/compiler-io/FIXTURES.md`](../../tests/compiler-io/FIXTURES.md), including
its Darwin error table and scalar-value precondition, extended by the
[review-2 literals and seed witnesses](../../tests/compiler-io/host/REVIEW-2.md).
No compiler capability
is added by this increment. IO source still needs the compiler executors'
strings, generics, closures, Base recognition and capability checks.

Run a module with:

```sh
BEND_NO_TELEMETRY=1 node scripts/run-wasm-io.mjs program.wasm sandbox -- arg1 arg2
BEND_NO_TELEMETRY=1 python3 -B tests/compiler-io/host-check.py
```

The sandbox is the program's virtual working directory. Arguments following
`--` are the entire program argument vector. Stdin is unused. Successful
completion prints nothing beyond the program's effects and exits 0. The
exported `runIO({modulePath, sandbox, args})` API also accepts raw `Uint8Array`
arguments and returns a typed completion record; the gate uses this to preserve
invalid UTF-8 argv and to inspect exit normalization before the OS masks it.

## Module and memory contract

A module exports exactly one unshared, 32-bit linear memory as `memory`,
`knot_alloc(i32 bytes) -> i32 address`, and `knot_main() -> ()`. Additional guest
exports are allowed. The memory declares a maximum no larger than 65,536 pages
(4 GiB, the wasm32 range; decision D19). A start section and imported memory are forbidden. The host validates
Wasm, checks imported and required exported function signatures, then instantiates
it. Only the imports below are permitted. Unknown imports return `Unsupported`
before any guest instruction runs.

All words are little-endian. Addresses, byte lengths, handles and U32 codes are
unsigned i32 bit patterns. Byte ranges are `[address, address + length)`,
without terminators. Empty ranges are allowed, including the memory-end
address. The host checks ranges by subtraction, avoiding wraparound. Result
records are aligned to four bytes; strings and byte ranges need no alignment.
A malformed address is an ABI failure, never a source-language `Invalid`.

Guest-to-host strings contain well-formed UTF-8 for Unicode scalar values.
`print`, `die`, paths and modes are checked with a fatal UTF-8 decoder that
preserves U+FEFF. Non-scalar or malformed input is `HostFailure io abi`.
Host-to-guest text is decoded with WHATWG UTF-8 replacement rules and then
encoded as canonical UTF-8. Every invalid maximal subpart, including an
incomplete final sequence, produces U+FFFD. A BOM remains U+FEFF. Each read
uses an independent decoder; bytes never carry over to the next read.

The guest reserves each 16-byte result record before calling an import:

| Offset | Word | Meaning |
| --- | --- | --- |
| 0 | `errno` | 0 for `Done`; a nonzero Darwin code for `Fail` |
| 4 | `value` | An open handle, returned read/write handle, or argument count |
| 8 | `address` | Returned bytes or argument descriptor array |
| 12 | `length` | Byte length of that range |

For `Fail`, the range contains the UTF-8 **message**, so the error is the pair
`(errno, message)`. A failing open has `value = 0`. A failing read/write retains
the input handle. Success on open/write has an empty byte range. Successful
read returns text. Success on args returns an array of `[address, byte_length]`
pairs; `value` is the number of pairs, and `length = 8 * value`.

The host allocates returned ranges by calling `knot_alloc`. It never retains a
guest memory view across that call: allocation may grow and detach memory.
The allocator must reserve disjoint, stable guest-owned ranges, may grow memory,
and must make no effect calls. The sole permitted callback is `exhausted(2)`.
An allocation failure must not return an alias or a wrapped pointer. Allocation
provenance and non-overlap remain the checked guest runtime's obligations;
range validation alone cannot prove them. Returned storage belongs to the
guest; the host retains no pointer after the import returns.

## Import module `knot_io`

Every parameter is i32; all imports have no Wasm result. `out` denotes a result
record. Effects finish synchronously before the next guest instruction.

| Import | Parameters | Behavior |
| --- | --- | --- |
| `args` | `out` | Returns arguments in order, including empty arguments, with no launcher/module name. |
| `print` | `address, length` | Writes exactly the string bytes followed by one LF to stdout. |
| `die` | `code, address, length` | Writes string plus LF to stderr and stops execution with `code mod 256`. It never resumes a continuation, even for code 0. |
| `open` | `path, path_length, mode, mode_length, out` | Opens relative to the sandbox using exactly `r`, `w`, or `a`; returns an opaque handle or an error pair. |
| `read` | `handle, maximum, out` | Reads at most `maximum` bytes from the current position, decodes that read independently, and returns the same handle and Result. |
| `write_bytes` | `handle, address, length, invalid, out` | Writes the complete byte range, or returns errno 22 without writing if `invalid != 0`. |
| `close` | `handle` | Consumes the handle. OS close errors are ignored, as in Base. |
| `exhausted` | `kind` | Runtime diagnostic, not a Base effect: 1 = step budget, 2 = allocation budget. Stops with `Exhausted`, exit 4. |

**Byte-list packing belongs to the guest.** A `List<&2,U32>` cannot be narrowed
unchecked. Scan the complete list, accumulating `invalid |= element >> 8`, and
copy each low byte into a fresh buffer. Only after the scan call `write_bytes`.
Thus byte lists cross as byte ranges, with one scalar validation flag; no list
layout or U32 array crosses the host ABI. A nonzero flag produces errno 22
before the buffer or write direction is used, with no file write. The compiler
must preserve this flag; a dishonest flag cannot be reconstructed from narrowed
bytes. The Wasm conformance runtime implements the scan; the unchecked-byte
mutant discards its flag at the host and is killed by the frozen `256` case.

**Handles.** Positive i32 tokens index a private host table. They are unrelated
to OS descriptors, are never reused during a run, and cannot designate stdin,
stdout or stderr. The checker must enforce affine transfer of `File`; host
range checking is not an affine type checker. Read and write return the same
live token; close retires it. Unknown/retired tokens are `HostFailure io handle`.
All remaining descriptors are closed when the run ends or fails. Dropping a
handle and halting after a write preserve already-written bytes.

**Open and error precedence.** NUL in the path returns 92 before inspecting the
mode. An unknown mode returns 22 before attempting filesystem access. An empty
path then returns 2. New files use mode 0644 subject to umask. `w` creates and
truncates; `a` creates and appends. A directory opens for `r`, fails with 21
under `w`/`a`, and fails with 21 on every read. Reading a write-only handle
returns 9. A nonempty write to a read-only handle returns 9. An empty write
returns `Done` without a syscall, including on read-only directory handles.
Invalid byte elements return 22 before checking the handle's direction.

| Darwin errno | Message |
| --- | --- |
| 2 | `No such file or directory` |
| 9 | `Bad file descriptor` |
| 20 | `Not a directory` |
| 21 | `Is a directory` |
| 22 | `Invalid argument` |
| 92 | `Illegal byte sequence` |

These messages are fixed strings, independent of Node's message capitalization,
path suffixes and libuv errno numbering. An OS error outside this qualified
six-error surface stops as `HostFailure io os`; it is not mislabeled as an
accepted Result or compiler rejection. Extending that surface requires a new
literal/seed witness.

**Ordering and bounds.** Output uses synchronous, complete writes. Earlier
stdout therefore precedes `die` in a merged pipe. File writes loop over short
writes; zero progress is a host failure. A regular-file read makes one syscall
with `min(maximum, remaining file bytes)`; this avoids a 4-GiB allocation for
`maximum = 4294967295`. Files are not concurrently modified during qualified
runs. A transfer/result allocation over 16 MiB is `Exhausted io memory`.
The suite's 1-MiB writes and 65,538-byte files fit. Resource exhaustion is
inconclusive; it never establishes source rejection or conformance.

## Sandbox and classification

The host resolves one existing directory as its root. All guest paths must be
relative, contain no `..` component, and contain no `.env` or `.env.*`
component under a case-insensitive comparison. This includes `.ENV`, `.Env`,
`sub/.Env.local` and `SUB/.env.LOCAL` in every supported mode, before an open
can read, truncate or append. The lexical check also refuses nonexistent
secret paths and applies on case-sensitive filesystems. It refuses symlinks
in any component, multiply-linked regular files,
and special files; only regular files and directories are supported. Final
opens use `O_NOFOLLOW`. Parent traversal, absolute paths and symlink escapes
are `HostFailure io sandbox`, distinct from the six language-visible errors.
These restrictions apply after the frozen NUL/mode/empty-path precedence.

The working directory must be private and stable during execution. Node's
path-based filesystem API does **not** provide an `openat` capability walk;
a concurrent external directory rename can race inspection. This is a working
directory sandbox for checked programs in an isolated workspace, not an OS
security boundary against a concurrent attacker. No networking or environment
lookup is exposed.

| Outcome | Exit | Meaning |
| --- | --- | --- |
| `Completed` | 0 | `knot_main` returned; its final Bend value was discarded by the guest. |
| `Halted` | 0..255 | Program `IO.die`; only the program's message is written. |
| `Unsupported` | 3 | An unlisted Wasm import was requested. |
| `Exhausted` | 4 | Explicit step/allocation limit or a recognized engine call-stack exhaustion. |
| `HostFailure` | 5 | Bad module/ABI, unknown handle, sandbox refusal, unmodeled OS failure or unexpected trap. |

Failures print `classification<TAB>io<TAB>code<LF>` to stderr. A program may
itself halt with 3, 4 or 5; the API's status distinguishes that from adapter
failure. No source is parsed here, so this adapter never produces `Invalid`.
Unexpected traps remain host failures, never alleged source errors or inferred
arena exhaustion. The CLI initializes its exit status to 5 and clears it only
with an explicit completed host result.

## Guest execution under D14

The VM makes **direct host calls from its guest execution machine**. The pinned
Base defines `IO(A)` in continuation-passing form:
`IO(A) = forall R. (A -> IO.OP<R>) -> IO.OP<R>`, and `IO.OP<R>` has only
`Emit{value: R}` and `Halt{code, message}`. In particular, `Emit` is the terminal
value, **not** an effect request. Foreign Base effects call the imports above;
`IO.pure`, `IO.bind` and the chosen closures are ordinary checked Base code.

IO construction must remain inert. The VM owns closure application, including
the nested continuation introduced by `IO.bind`, and its explicit call and
continuation state. Its dispatch loop performs transitions; imports return
results to the guest's continuation. No guest frame, closure layout or
serialized instruction crosses this ABI. `Halt` calls `die`; terminal
`Emit` returns from `knot_main` after discarding its value. Dropped actions and
unchosen closures never become machine states and execute no effects.

Neither walking a left-associated bind nor applying a right-associated
continuation may recurse through Wasm or JavaScript calls. The machine must
also trampoline **construction/application** of CPS closures: eliminating only
the final effect loop would leave a 100,000-deep pure bind chain vulnerable.
The pending frames occupy guest storage. Budget checks report exhaustion;
they must not silently cut the chain short. The VM design fixes its own
representation and proves/tests its transitions. Direct native Wasm emission
may use D3's defunctionalized closures on the speed track and call the same
imports; that lowering is not a prerequisite for this host or D14 self-hosting.

The compiler follow-up must recognize only the hash-pinned Base foreign
identities, fully check its supported source forms, validate reachable host
capabilities before emission, and implement scalar/string/list conversion.
Checking a source, choosing a valid import name, and passing the host ABI gate
are separate obligations. The 11 seed-rejected and six Knot-Unsupported
fixtures retain their frozen compiler expectations.

## Independent conformance runtime

[`host/PLAN.json`](../../tests/compiler-io/host/PLAN.json) was written before the
host implementation. It selects 20 existing fixtures, **86 runs**, all six
errnos, both 100,000-bind directions, six mutants and initially 18 literal host controls.
Expected observable results come exclusively from the already-frozen
`expectations.json`. No host observation generates an expectation.
The six argument runs also execute through the real CLI, including raw invalid
UTF-8 OS arguments, rather than only through the byte-preserving API harness.
A nineteenth control was added during review: allocator callbacks cannot
perform effects, including `close`. Its expected ABI failure was fixed before
repairing the missing close guard; the prior host reported a handle failure.

[`host/runtime.wat`](../../tests/compiler-io/host/runtime.wat) interprets an
explicit serialized description tree with `Emit`/`Halt` terminals, deferred
foreign calls and bind frames. This is a test representation for defunctionalized
IO, not a new claim about Base's `IO.OP` constructors. The serializer only
encodes hand translations using fixture arguments; it does not parse Bend or
read seed results. String reports, scalar enumeration, read summaries, result
branches and the deep-bind totals are computed by Wasm from actual host
responses. `wat2wasm` assembles the test runtime; it is not a compiler dependency
for Knot emission.

Each node is eight aligned i32 words. Node addresses are absolute memory
addresses. Unused words are zero. Serialization begins at address 4096; address
64 holds the current ABI result. The root, initial heap and fuel budget are
baked into each test module. Constant strings and U32 lists live in the same
serialized data segment.

| Tag | Description | Following words |
| --- | --- | --- |
| 0 | Emit / resume with a pure value | `value` |
| 1 | Bind | `action_address, continuation_address` |
| 2 | Deferred foreign call | `effect, operands...` |
| 3 | Halt | `code, string_address, byte_length` |
| 4 | Increment continuation | `delta` |
| 5 | Report continuation | `format, prefix_address, prefix_length` |
| 6 | Fail-to-Halt continuation | `exit (0 uses errno), prefix_address, prefix_length` |
| 7 | Argument report continuation | none |
| 8 | Result branch | `failure_address, success_address` |

Deferred effects are args=0, print=1, open=2, read=3, write=4, close=5. Print
operands are a byte range, open uses two string ranges, read uses a maximum,
and write uses the test-only U32 input array and its element count. Write
packing occurs inside Wasm before the ABI call. Reports use text=0, scalar
codes=1, scalar count/last=2, Result=3, accumulated U32=4, read Result=6.

The interpreter loop pushes/pops explicit frames. The left-bind stress fills
100,000 pending frames; the right-bind stress repeatedly selects a continuation.
Both compute 100,000 by actual additions and match the seed's two printed
reports. Constant-output substitution cannot satisfy this particular machine
execution. This is bounded executable evidence, not a formal proof of a future
compiler's closure transformation.

## Gate and remaining work

Gate `io-host` runs `regen.py` **in verify mode first**, then compares each
covered run's entire `exit`, stdout/stderr or merged `output`, and final
sandbox `files` record, including sizes, hashes, inline bytes and seeded-file
change flags. It also requires a `Completed`/`Halted` API outcome with the
normalized exit. The host outcome check kills the unmasked-256 mutant even
though a process exit alone would hide it by OS truncation.

All six mutants preserve the import signatures, pass Node syntax checking,
and execute valid, engine-validated Wasm. Each must produce a wrong semantic
observation while still completing/halting; a crash, missing tool, malformed
module or adapter failure is not a mutant kill. The mutations are UTF-16-unit
encoding, dropping truncated UTF-8 replacement, unmasked exit, allowing read
on a write handle, ignoring invalid byte elements, and omitting print's LF.

Literal controls cover import/export signatures, start sections, malformed and
missing modules, ranges/alignment, scalar preconditions, handles, path escapes,
explicit step/allocation exhaustion, and unexpected traps. Receipts are in
[`tests/compiler-io/receipts/host.json`](../../tests/compiler-io/receipts/host.json),
with source/seed/module hashes and tool versions. The gate runner registers this
receipt and exact coverage counts. Shared compiler receipts are left to the
coordinator.
The census registry and its dependent hash were regenerated for `io-host`.
Its existing IO/sugar adapter warnings remain explicit; host conformance does
not promote either suite to accepted compiler features. No source, import or
feature-class approval changed.

The original host increment changed no Bend declarations. Review 2 adds one
independent seed fixture (seven definitions, no new laws). Its bounded offline
preflight has zero structural blockers, complete role context and composition,
and zero provider requests. This is not a live style rating or an automatic
style pass. The existing proof entries still run inside their gates.

Review 2 adds four empty-write Wasm observations and 12 fresh seed observations
(interpreter/native/emitted JS), 21 secret-path controls (seven spellings by
three modes), and 14 oracle controls. Twelve synthetic fault controls cover
stdout/stderr/merged output, exits 0/1, and either pass of `--write`; two
ordinary-result controls preserve non-fault exit 0/1 observations. Three new
semantic mutants restore case-sensitive filtering, restore empty-write errno 9,
and allow seed memory faults to be frozen. All are killed by the fixed
controls, not by an infrastructure failure. The original 86 runs, six CLI
runs, 19 boundary controls and six mutants remain unchanged.

`regen.py` aborts on any seed stream containing `bend: memory fault` before
writing expectations. Such faults are lane exhaustion, never expected program
behavior. Existing IO oracles remain bounded to completing JS-lane runs;
compiler-sized C1 inputs use the native lane under D14. Before CLI budgets
grow, its owner must replace the post-write `List.length(bytes)` and audit
similar output-sized non-tail traversals. Host repair does not raise budgets.

Next: connect the VM's checked image execution to `knot_io`, and run **all 103
agree runs** plus the review-2 cases through compiler-produced images and the
VM. Retain the complete frozen Invalid/Unsupported compiler checks and add an
independent IO evaluator comparison when that lane exists. This increment
does not exercise the four remaining agree fixtures
(`mini-driver`, `bind-order`, `bind-lazy`, `result-bind`), general captured
closures, source quantity rejection, or an IO evaluator lane. Add allocator
ownership/reclamation evidence, broader OS error witnesses and stronger
filesystem isolation if the execution threat model expands.

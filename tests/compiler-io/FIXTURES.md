# IO fixture suite (frozen)

These are the frozen expectations for the IO host ABI of campaign milestone 10,
**Whole compiler as Wasm** ([charter](../../docs/COMPILER-CAMPAIGN.md)). Under D7
they were fixed before implementation and independently of the implementer.
Seed-accepted and seed-rejected outcomes come from the pinned seed, Bend 2.0.29
at `574b6d3`. Knot-specific outcomes come from literal review. Nothing in this
directory was derived from Knot's output. Under D4, a form Knot cannot yet check
is `Unsupported`, never `Invalid`, and never passed through unchecked.

| File | Role |
|---|---|
| `fixtures/*.bend` | 40 whole programs with `main`. Each imports Base, is ASCII with LF endings, has no raw tab, and reuses no Base name. |
| `fixtures/inputs/*` | 15 input files, copied into run sandboxes. `.gitattributes` marks them binary. |
| `expectations.json` | Per fixture: its hash, the seed's `--check-only` record, and every run's argv, sandbox inputs, command, exit status, stdout, stderr and final sandbox files, plus the Knot outcome. |
| `regen.py` | Re-runs the seed and fails on any difference from `expectations.json`. |

## Runs

A fixture the seed accepts is run once per planned run. A fixture it rejects is
run once without arguments (`seed_run`) to show that nothing executes.

- **Sandbox.** Each run gets a fresh, empty directory,
  `.local/compiler-io/runs/<fixture>/<run>/` (ignored). It is seeded only with the
  files named in the run's `inputs` (sandbox path to `fixtures/inputs/` name), and
  it is the working directory. Every path a program uses is relative to it.
- **Command.** `bun ../../../../../.toolchain/bend-2.0.29-574b6d3/bend2/main.ts
  ../../../../../tests/compiler-io/fixtures/<fixture>.bend -- <argv...>`. The
  launcher treats a leading `-` as its own option, so the harness always passes
  `--`. The program sees exactly `argv`.
- **Environment.** `BEND_NO_TELEMETRY=1`. Every other `BEND_*` variable and
  `KNOT_IO_FIXTURE_UNSET` are removed. Stdin is `/dev/null`.
- **Record.** `exit`; `stdout` and `stderr` (or `output`, when a run merges both
  streams into one pipe); and `files`, which lists every file and directory left
  in the sandbox, seeded inputs included. A seeded file notes `seeded_from` and
  whether it `changed`. A byte blob always carries `size` and `sha256`. A small
  blob also carries its bytes: `text` when they are valid UTF-8, `hex` otherwise.
  The limits are 4,096 bytes for streams and 1,024 for files.
- **argv.** An argument that is not valid UTF-8 is recorded as `{"hex": ...}` and
  passed as those raw bytes.
- **Reviewed literals.** Every run's exit status is written in `PLAN` by hand
  from the ABI below. So are its stream text and chosen files: 26 exact file
  contents and 5 required absences. `regen.py` fails if the seed disagrees with
  any of them. A run's `reviewed` list names the fields it fixed. Some literals are
  computed rather than typed: the 256-byte and 1,048,576-byte outputs of
  `write-bytes` must equal `bytes(i & 255 for i in range(n))`, and the argument
  and read reports decode their bytes with Python's own UTF-8 decoder.

## The host ABI these fixtures define

A Knot IO program is a checked book whose `main` takes no parameters and has
type `IO(A)`. The host runs `main` and serves the operations below, in program
order, to completion. The compiler uses exactly six foreign Base effects
(census of the non-law `src/*.bend` files): `IO.args`, `IO.print`, `File.open`,
`File.read`, `File.write_bytes` and `File.close`. `IO.bind`, `IO.pure` and
`IO.die` are ordinary Base definitions over `IO.OP` (`Emit` and `Halt`), as are
`IO.pass` and `IO.try`. This suite fixes the observable contract, not the Wasm
import names, buffer layout or handle representation. Any shape that reproduces
every record conforms.

**Encodings.**

- `String` is a sequence of Unicode scalar values (Chars), never UTF-16 units.
  It crosses to the host as UTF-8.
- Bytes crossing into a `String` (`args`, `read`) are decoded as WHATWG UTF-8.
  Each maximal invalid subpart becomes one U+FFFD, a truncated sequence at the
  end becomes one U+FFFD, and a BOM stays as U+FEFF.
- A byte list is `List<&2,U32>`, one byte per element.
- A host failure is `Fail{(code, message)}` of type `U32 & String`. `code` is
  the platform errno and `message` is its `strerror` text.

**Operations.**

| Operation | Contract |
|---|---|
| `IO.args() -> IO(List<String>)` | The program arguments in order: no program or launcher name, empty strings kept. Invalid UTF-8 bytes decode to U+FFFD. |
| `IO.print(s) -> IO(Unit)` | Writes UTF-8(`s`) then one LF to stdout, before the next effect starts. |
| `IO.die(A, code, msg) -> IO(A)` | Runs no further effect and never resumes its continuation. Writes UTF-8(`msg`) then one LF to stderr. The exit status is `code mod 256`: 256 exits 0, and 4294967295 exits 255. Code 0 still writes the message. Earlier stdout stays, and in a merged stream it precedes the message. |
| completion of `main` | Exit status 0. The final value of any `A` is discarded, and nothing more is written. |
| `File.open(path, mode) -> IO(Result<..,File>)` | A path containing U+0000 fails with 92 before the mode is examined. The mode must be exactly `r` (read), `w` (write, create, truncate) or `a` (write, create, append), and anything else fails with 22. Then the OS opens the path relative to the working directory. An empty path fails with 2, a missing path or parent with 2, and a non-directory parent with 20. A directory opens under `r` and fails with 21 under `w` or `a`. |
| `File.read(f, max) -> IO(File & Result<..,String>)` | One read of at most `max` bytes from the current position, decoded alone and returned with the handle. The rest waits for the next read, and end of file gives `""`. `max` 0 gives `""`. `max` 4294967295 simply returns what is there. A handle opened `w` or `a` fails with 9. A directory fails with 21, again on every retry. |
| `File.write_bytes(f, xs) -> IO(File & Result<..,Unit>)` | If any element exceeds 255, the call fails with 22 and writes nothing. Otherwise it writes every byte, 0 to 1,048,576 of them, at the position, or at the end under `a`. A handle opened `r` (a directory included) fails with 9. |
| `File.close(f) -> IO(Unit)` | Answers `Unit`; the seed ignores close errors. Dropping a handle without closing it loses no written bytes, including when `IO.die` follows. |

**Error codes** (Darwin arm64 values; `regen.py` refuses any other platform):

| Code | Message | Raised by |
|---|---|---|
| 2 | `No such file or directory` | open: missing path, missing parent, empty path |
| 9 | `Bad file descriptor` | read on a `w`/`a` handle; write on an `r` handle |
| 20 | `Not a directory` | open through a file used as a directory |
| 21 | `Is a directory` | open `w`/`a` on a directory; read on a directory |
| 22 | `Invalid argument` | open with an unknown mode; write_bytes with an element above 255 |
| 92 | `Illegal byte sequence` | open of a path containing NUL (glibc would give 84) |

**Sequencing.**

- `IO.bind(A, B, m, f)` performs `m`'s effects, then those of `f(value)`.
- An IO value is a description. It runs where it is bound, never where it is
  built, and a dropped one never runs.
- Continuations may be bare definition names, partial applications or
  capturing lambdas.
- 100,000 right-nested and 100,000 left-nested binds must complete.

**Precondition, not a fixture.** Every Char that reaches `print` or `die` is a
Unicode scalar value. The seed's two lanes disagree beyond that. In the JS lane,
the lane these records come from, printing `"\u{d800}"` exits 1 with
`bend: 55296 is not a Unicode scalar value` after the earlier output. The native
lane's source instead encodes such Chars as generalized UTF-8. The
precondition is safe for self-hosting: Knot's diagnostics are ASCII, and
`File.read` produces only scalar values.

## Coverage

Fixture names omit the directory and `.bend`. K marks a Knot-specific
`knot_expected` outcome.

| Feature | Positive | Edge | Negative |
|---|---|---|---|
| print | `print-lines` | `print-large`, `print-many` | `print-non-string` |
| args | `args-echo` (none, many, non-ASCII, blank, dash-led, invalid UTF-8) | | |
| die | `die-messages` | `die-codes`, `die-stops-effects`, `die-after-write` | `die-nat-code` |
| open | | `open-modes`, `open-nul-path` | |
| read | `read-text` | `read-limit`, `read-decode` | `reuse-file`, `forge-file`, `read-result-without-handle` |
| write | `write-bytes`, `write-read-back` | `write-values`, `handle-dropped` | `write-bytes-string`, `write-bytes-affine-list` |
| driver | `mini-driver` | | |
| sequencing | `bind-order` | `bind-lazy`, `bind-deep`, `main-value` | `reuse-io`, `bind-non-io-continuation` |
| Result | `result-try`, `result-bind` | | `result-missing-fail` |
| Outside the increment (K) | `effect-write`, `effect-print-err`, `effect-get-env`, `effect-file-write`, `do-bind-arrow` | | `do-bind-type-mismatch` |

The requested cases map to runs as follows:

| Case | Runs |
|---|---|
| Printing | `print-lines`, `print-large` (100,000 characters), `print-many` (5,000 lines) |
| Arguments | `args-echo`: `none`, `many` (16), `unicode`, `blank`, `dashes`, `invalid-utf8` |
| Exit codes | `die-codes`: 0, 1, 2, 3, 4, 5, 255, 256, 4294967295 |
| Small, empty and missing reads | `read-text`: `small`, `empty`, `unicode`, `unicode-path`, `missing`, `directory`, `not-directory`, `empty-path` |
| Read at and over the limit | `read-text`: `at-limit`, `over-limit`; `read-limit`: 65,536, 65,537 and 65,538 bytes against the driver's 65537, `straddle`, `zero`, `max-u32` |
| Writing bytes | `write-bytes`: `empty`, `all-bytes` (0..255), `large` (1,048,576), `truncate`; `write-values` |
| Effect order | `bind-order`, `bind-lazy`, `bind-deep`, `die-stops-effects` (`merged`), `write-read-back`, `mini-driver` (`same-path`) |
| Error propagation | `read-text`, `mini-driver` (HostFailure for each stage), `result-try` (errno as exit status), `result-bind` |

The seed accepts 29 books and rejects 11. There are 109 runs: 103 on the 24
fixtures Knot must agree with, and 6 recorded on seed-accepted `Unsupported`
fixtures. Negatives name a seed-valid `twin` and the `seed_reason` substrings
their rejection must contain. `regen.py` fails if the seed rejects one for
another reason.

## Knot outcomes

- **`knot: agree`** (24 fixtures). The book checks, and `compile-cli` builds a
  module. Run under Knot's IO host adapter, each run must reproduce the recorded
  `exit`, the stdout and stderr bytes (or the merged `output`), and the complete
  final sandbox file list with its bytes. The run uses the recorded argv, empty
  stdin, and a fresh sandbox seeded with the same inputs as its working
  directory. Only the command line that starts the program differs from the
  seed's. The Wasm lane is the required lane. The pure evaluator (`eval-cli`)
  owes nothing for IO mains in this increment. If an IO-interpreting evaluator
  lane is added, it owes the same records. This is a coordinator decision and
  may be vetoed before implementation starts.
- **`knot: Invalid`** (10 fixtures). The seed rejects the book. Knot exits 2
  with an `Invalid` diagnostic and emits no artifact. Phase and code are open to
  the implementer. The seed's exact message is recorded as evidence.
- **`knot_expected: Unsupported`** (6 fixtures). These are reviewed literals.
  Knot exits 3, the diagnostic starts with the recorded prefix, and no artifact
  is emitted. The seed's own result is kept alongside.

| Fixtures | Prefix | Justification |
|---|---|---|
| `effect-write`, `effect-print-err`, `effect-get-env`, `effect-file-write` | `Unsupported\tcheck\thost-effect\t` | The ABI is the compiler's own six effects. S4 of `BEND-SUBSET-STAGES.md` maps only the declared Base effects the driver needs, and D4 forbids passing any other foreign effect through unchecked. Every other Base foreign definition takes this prefix too, including `File.read_bytes`, `File.size`, `Process.run`, channels, sockets and windows. |
| `do-bind-arrow`, `do-bind-type-mismatch` | `Unsupported\tparse\tdo-bind\t` | Knot's own `do` blocks hold statements only: the census finds no `<-` and no `return` in `src/*.bend`. The second fixture is seed-invalid, but D4 forbids an `Invalid` claim about a form Knot does not check. |

In these prefixes, `\t` stands for a tab character; `expectations.json` holds
the exact strings. Both scope calls **may be vetoed before implementation
starts**. If they are, change `knot` in `PLAN` (the host-effect fixtures to
`AGREE` with runs reviewed as for the others; `do-bind-arrow` to `AGREE` and
`do-bind-type-mismatch` to `INVALID`), then re-freeze. After implementation
starts, changing any expectation requires a recorded review. Implementation
results never justify one.

## Dependencies the implementer should see up front

The fixtures are written in the register of `src/driver.bend` and the CLIs.
They use explicit type arguments to `IO.bind`, statement-only `do IO<..>:`
blocks, `(file,result) = pair`, and `case Fail{(code,message)}`. They therefore
need:

- **Milestone 3.** Nested `Con` argument patterns, `case _`, the multi-scrutinee
  match in `write-values`, and `Fail{Problem{code,message}}` in `result-bind`.
- **Milestones 5 and 6.** String escapes including `\0`, `\r` and `\u{..}`;
  Nat literals up to `100000n`; `Result<&1,&1,U32 & String,File>`, pairs and
  `Maybe<&2,U32>`.
- **Milestone 7.** Partial applications such as `opened(max)` and `first(max)`,
  and capturing lambdas.
- **Milestone 8.** The reachable Base slice: `String.concat`, `append`,
  `length`, `repeat` and `eq`; `U32.show`, `read`, `add`, `sub`, `and`,
  `is_zero`, `to_nat` and `from_nat`; `Char.to_u32`; `IO.pure`, `IO.try` and
  `IO.pass`.
- **Storage.** `write-bytes` `large` holds a 1,048,576-element byte list, and
  `bind-deep` performs 200,000 binds. Neither fits the one-page arena of
  `knot-fields-wasm-1`. A run that reports `Exhausted` is inconclusive and never
  a pass. It is no reason to edit the fixture.

## Seed behaviour worth knowing

- **`List.length` overflows the JS lane.** `List.length(&2,U32,xs)` recurses
  without a tail call. At 65,536 elements, and at every larger size tried, it
  faults with `bend: memory fault (machine stack overflow?)` and exits 1.
  `src/compile-cli.bend` reports its Built count with
  `U32.from_nat(List.length(&2,U32,bytes))` after the write. `write-bytes`
  therefore reports the requested count instead. The file had already been
  written in full when the fault came. Whether compile-cli is affected on its
  build lanes was not measured here.
- **`IO.get_env` on an unset variable** answers `Fail{(2, "No such file or
  directory")}`.
- **File creation mode.** The seed opens new files with mode 0644, before the
  umask. No record observes permissions.
- **`main(x: U32) -> IO(Unit)` is not an IO program to the seed.** The seed
  prints the normalized lambda instead of running it. No fixture relies on this.

## Regenerating and verifying

From the repository root, on Darwin arm64 with Bun 1.3.14 and the pinned
toolchain at `.toolchain/bend-2.0.29-574b6d3`:

```sh
python3 tests/compiler-io/regen.py          # verify; exit 0 only on a byte-exact match
python3 tests/compiler-io/regen.py --write  # re-freeze after a reviewed change
```

Every command has a 120-second timeout. A timeout aborts the script and is never
recorded as a result. Verification fails in any of these cases:

- a seed file changes: `main.ts`, `bend.ts`, `comp.ts`, `base.bend`, or one of
  the nine JS effect sources used;
- the Bun version or the platform changes;
- a fixture or input is edited, added or removed, or an input is unused;
- a `PLAN` entry changes;
- a reviewed literal disagrees with the seed;
- a negative is rejected for another reason;
- any output leaks a local path;
- a local name reuses a Base name.

`--write` builds the document twice and writes only if both builds agree. A full
run takes about ten seconds with six parallel jobs.

## What the implementer wires

The gate runner belongs to the implementer. It should:

1. Run `regen.py` in verify mode first. A mismatch means the frozen evidence
   moved, and the gate stops.
2. For each `knot: agree` fixture:
   - `check-cli` reports `Checked`;
   - `compile-cli` builds the module;
   - each run executes under the IO host adapter in a fresh sandbox seeded from
     `inputs`, and matches the recorded `seed` record field by field.
3. For each `knot: Invalid` fixture, run check and compile. Each must exit 2
   with an `Invalid` diagnostic and leave an existing output file untouched.
4. For each `knot_expected` fixture, the result must be exit 3, the exact
   `diagnostic_prefix`, and no artifact.
5. Record receipts in the style of `tests/compiler-wasm/receipts/`. Never edit
   `expectations.json` to match Knot.

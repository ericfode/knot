# knot-io-2 fixture contract

These literals are fixed before changing `scripts/run-wasm-io.mjs` from
`f42ae39`. They extend the host boundary under D17, not the source language.
The existing IO suite, its 86 host runs and review-2 assertions stay unchanged.

`expectations.json` fixes 11 byte fixtures, 26 identity fixtures, 23 boundary
controls and four semantic mutants. Expectations come from literal byte and
protocol review. The two unmodified foreign bodies in `reference/` are copied
from `campaign/modules` commit `0111f13`; their SHA-256 identities are fixed in
the manifest. The gate executes both bodies independently of the new host.
It never regenerates expectations from host observations.

## Imports and records

`read_bytes(handle, maximum, out)` has three i32 parameters and no result.
It has the same result record, handle checks, cursor, unsigned maximum and
16 MiB transfer bound as `read`. It returns the bytes read without decoding,
BOM removal, replacement or encoding. `read` and `read_bytes` advance the same
file position by the number of input bytes consumed. A zero-length read does
not advance it. Direction and directory errors still precede that empty read.

`path_identity(path, length, out)` has three i32 parameters and no result.
Success sets errno 0, value 0 or 1, address 0 and length 0. It is a query;
`false` is a successful result, not `Invalid` or a host error. The guest loader
classifies it. Failure sets value 0 and returns the Darwin errno/message pair.
NUL returns errno 92 before path policy; invalid UTF-8 is an ABI failure.

Identity examines components in spelling order, before path normalization:

- Empty and `.` components do nothing. `..` steps to the parent only after all
  preceding components have been examined.
- An existing symlink returns false immediately, including a dangling link,
  a link out of the sandbox, or a link before `..`.
- Every existing component must equal an actual directory entry byte for byte.
  On a case-insensitive filesystem a case alias returns false. On a sensitive
  filesystem an absent differently-cased name instead reaches the missing rule.
- ENOENT and ENOTDIR return true immediately. Opening a path decides whether it
  exists and is readable. Consequently `missing/../link-file` returns true.
- Hardlinks and special files are identities; the independent `open` policy
  still refuses them. Identity does not follow links or read file contents.

The sandbox is the query's working directory. Internal parent steps and
absolute paths within its canonical root are permitted for this query.
An absolute path outside that root or a lexical step above it is
`HostFailure io sandbox`. This host restriction bounds parity with the foreign
bodies; it is not a different definition of canonical identity. The unchanged
`open` import continues to accept relative paths without `..` only.

All spellings of `.env` and `.env.*` remain forbidden, case-insensitively,
including components after an absent path. Secret-path tests use nonexistent
names; they do not create, read or copy a secret file. NUL has precedence.
The private, stable-directory and race limits of knot-io-1 still apply.

`exhausted(3)` terminates with the typed record
`{status: "Exhausted", code: "frames", exit: 4}` and writes
`Exhausted\tio\tframes\n`. No later guest instruction executes. Kinds 1 and 2
and the recognized engine `call-stack` outcome are unchanged. Other kinds are
ABI failures. Allocation callbacks still permit only exhaustion kind 2.

## Independent observations

Byte fixtures pin empty reads, every byte value, invalid UTF-8, non-BMP UTF-8,
a BOM, split sequences, unsigned maxima, EOF, mixed text/raw reads, handle
errors and growth across a Wasm memory page. Returned handle/value, bytes,
length and the zero pointer for empty results are observed through valid Wasm.
The private input bytes and filesystem entries must remain unchanged, except
for the explicitly opened write/append fixtures.

Identity fixtures run against the frozen C body, frozen JS body and the real
Wasm import on the same private tree. The C harness extracts the query helper;
its NUL guard matches the frozen foreign wrapper. The JS harness supplies only
the foreign runtime's byte/result adapters. Filesystem case sensitivity is
measured and recorded; both possible expectations are fixed in the manifest.
No source checker/evaluator or VM image lane exists for these new imports yet.

The two required mutants decode raw reads and ignore identity, respectively.
Both must execute valid Wasm and complete normally with a wrong result. The
additional case-comparison mutant must disagree on a case-insensitive volume;
the frame mutant must return a wrong, explicit Exhausted classification.
Crashes, invalid Wasm, syntax errors and unavailable tools do not kill mutants.

No Bend file or law is added. Offline style preflight has zero changed Bend
targets. Live review and compiler/VM integration belong to subsequent owners.

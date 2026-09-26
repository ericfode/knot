# Source specification

Source is an immutable sequence of Unicode scalar values identified by a
caller-supplied U32 file ID. The owned handle is affine; scalar observations,
cursors, locations and spans are Data. Obtain handles only through new/bounded.
Implementation constructors and helper functions are unsupported internals.

## Units and identity

Offsets, lengths, span bounds and zero-based columns count scalars/codepoints.
They do not count UTF-8 bytes, UTF-16 code units, graphemes or display cells.
No normalization is performed. Source does not decode bytes. In particular an
astral character occupies one offset here and two UTF-16 units upstream; no
implicit conversion or UTF-16 bridge is offered.

The caller assigns a unique file ID per immutable source revision in its session.
Two equal IDs mean the same revision. This package cannot detect ID reuse with
other content; it is not an allocator, path canonicalizer or content hash.
A span or cursor with another file ID fails with ForeignFile before bounds checks.

## Public operations

See INTERFACE.md for exact Bend signatures and import paths. Only Source and
Source.maximum/new/bounded/file/length/line_count/text/get/cursor/peek/bump/
checkpoint/restore/span/extract/locate/offset are API, together with types.bend's
Error, Cursor, Span and Location. Helper declarations are not supported API.

- new/bounded preserve every scalar in order. The effective limit is the lesser
  of the requested limit and 16,777,215. The line index needs n+1 Vec slots, up to
  Vec's 16,777,216 limit. Limit zero accepts only empty content.
- Validation proceeds left to right. At each character scalar validity is checked
  before capacity; the first failure wins. Surrogates U+D800..U+DFFF and values
  above U+10FFFF fail with InvalidScalar where the backend can represent them.
  JS's upstream Char constructor rejects these before Source receives them.
  An exceeded policy limit is Limit; host allocation failure is not recoverable
  through this API. Construction may still traverse the input after failure.
- file, length, line_count, text return exact metadata/content with the source.
  No public operation mutates any source content, ID, length or line index.
- get accepts exactly offsets less than length; all others return Bounds.
- cursor and restore accept offsets at most length. checkpoint copies the exact
  file ID and offset. At a valid non-EOF cursor, peek returns Some(original[i]);
  bump returns that same character and cursor (file,i+1). At EOF both return
  None and bump preserves the cursor. Invalid cursors fail, preserving the source.
- span creates (file,start,end) iff start <= end <= length. extract validates ID
  and bounds, then returns exactly the half-open subsequence in original order.
  Empty ranges including [length,length) succeed. Bounds failures are InvalidRange.
- Line zero starts at offset zero, even for empty input. Each LF adds a line start
  at the next offset. CR is ordinary content; CRLF has one break after LF. LF
  belongs to the preceding line. A trailing LF creates an empty final line.
- locate accepts every offset through EOF. Its line is the greatest line start
  <= offset; its column is offset minus that start. offset is the inverse on
  canonical locations: a nonfinal line excludes the next line start, while the
  final line includes EOF. Missing lines and noncanonical columns return Bounds.
  Validation compares column with available width before addition, preventing wrap.
- IndexInvariant reports an impossible internal line-index read or exhausted
  search bound. It cannot be produced by a source obtained through the API under
  the Vec contract. It is never translated into a successful partial location.

## Abstraction and cost

The abstraction relation is: chars equals the scalar sequence; cached size equals
its length; starts equals [0] followed by i+1 for every LF at position i; file equals
its caller ID. model.bend independently walks a linked String, scans its prefixes
for positions, and enumerates positions for reverse lookup. It imports no Vec,
main implementation, line index, or binary search. Runtime observations compare
public results with this model and verify retained text after operations.

With pinned native Vec/Array lowering: construction O(n) amortized; get, cursor,
peek, bump, checkpoint, restore, span, metadata and offset O(1); locate O(log L)
for L lines; text O(n); extract O(range length). Space is O(n+L). Binary search
halves [lo,hi), where start[lo] <= position and hi is exclusive. L <= 2^24 needs
at most 24 midpoint probes plus a finishing step; 25 fuel is sufficient. Failure
is explicit if this bound is unexpectedly exhausted. No list indexing is used
for source reads or line lookup. Vec owns allocation and bounds enforcement.

Timings are supporting evidence, not complexity proofs. Compiled CPU and JS are
verified; GPU and Knot's future Wasm/WebGPU execution are untested. No lexer,
parser, general filesystem interface, byte decoder, or editing buffer is included.

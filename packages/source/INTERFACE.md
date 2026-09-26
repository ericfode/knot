# Source interface

2026-09-26: published and verified on CPU and JS.

```bend
import 0x88d5b48c03f82f217d3a2aa0656744f4/main.bend as S
import 0x88d5b48c03f82f217d3a2aa0656744f4/types.bend as T
```

Vec is pinned to 0xd684886d10b431b9dce6c3b2d1ef1980. See STATUS.md and
LAW_REVIEW.md for exact validation evidence.

Pure owned Source built from a Bend String, using Vec's public interface only.
Offsets, lengths and zero-based columns count Unicode scalar values (codepoints),
not bytes, graphemes, display cells or UTF-16 units. No implicit conversion to the
upstream compiler's UTF-16 positions is provided. LF starts a line; CR is ordinary
content, including in CRLF. The empty input has one line. EOF is a valid position.

Stable API (operations under Source; value types in types.bend):

```
Source : Type
Error : Data = Bounds | ForeignFile | InvalidRange | InvalidScalar | Limit | IndexInvariant
Cursor : Data = Cursor{file: U32, offset: U32}
Span : Data = Span{file: U32, start: U32, end: U32}
Location : Data = Location{line: U32, column: U32}
Source.maximum() -> U32
Source.new(file: U32, text: String) -> Result<Error,Source>
Source.bounded(file: U32, text: String, limit: U32) -> Result<Error,Source>
Source.file(s: Source) -> Source & U32
Source.length(s: Source) -> Source & U32
Source.line_count(s: Source) -> Source & U32
Source.text(s: Source) -> Source & String
Source.get(s: Source, offset: U32) -> Source & Result<Error,Char>
Source.cursor(s: Source, offset: U32) -> Source & Result<Error,Cursor>
Source.peek(s: Source, c: Cursor) -> Source & Result<Error,Maybe<Char>>
Source.bump(s: Source, c: Cursor) -> Source & Result<Error,Cursor & Maybe<Char>>
Source.checkpoint(c: Cursor) -> Cursor
Source.restore(s: Source, checkpoint: Cursor) -> Source & Result<Error,Cursor>
Source.span(s: Source, start: U32, end: U32) -> Source & Result<Error,Span>
Source.extract(s: Source, span: Span) -> Source & Result<Error,String>
Source.locate(s: Source, offset: U32) -> Source & Result<Error,Location>
Source.offset(s: Source, location: Location) -> Source & Result<Error,U32>
```

Source constructors/internal helpers are unsupported implementation details;
callers obtain Source through new/bounded. Cursor/Span/Location may be constructed
by callers: operations always validate them. File IDs are caller-assigned unique
within a compilation session; equal IDs denote the same immutable file revision.
This is not a global identity allocator or a content hash. Reusing an ID for
different text violates the caller contract and cannot be detected by this core.

Bounded clamps limit to 16,777,215 codepoints (line index requires n+1 Vec slots).
Invalid scalar values (surrogates or above U+10FFFF) fail construction. Limit 0
accepts empty input. No successful operation changes source content or identity.
EOF peek returns Done(None); EOF bump returns the unchanged cursor and None.
Invalid cursor/spans return errors; ForeignFile takes precedence over bounds.
Span bounds are half-open 0 <= start <= end <= length. Range errors use InvalidRange.
Location lookup includes EOF. Reverse lookup requires canonical locations:
nonfinal lines end before the next line's start; the final line includes EOF.

Target costs under native Vec lowering: construction O(n), get/peek/bump/cursor,
checkpoint/restore/span/metadata O(1), locate O(log lines), offset O(1),
text O(n), extract O(span length). No filesystem, lexer, parser, UTF decoder,
or GPU execution claim.

IndexInvariant is reserved for an impossible internal line-index failure. No
public valid-source path is expected to return it; it is never a partial success.
Source.maximum returns the source policy maximum, 16,777,215.

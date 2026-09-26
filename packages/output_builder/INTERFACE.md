# OutputBuilder interface

Stable initial API; Base only. Published hash is recorded in RELEASE.json.
Local imports: `import ./main.bend as Text`, `import ./bytes.bend as Bytes`.
Remote imports: `import <hash>/main.bend as Text`, `<hash>/bytes.bend as Bytes`.

## Text

`Text.Builder` is persistent Data. Operations:

- `empty() -> Builder`
- `fragment(text: String) -> Builder`
- `append(builder: Builder, text: String) -> Builder`
- `character(builder: Builder, char: Char) -> Builder`
- `compose(left: Builder, right: Builder) -> Builder`
- `finish(builder: Builder) -> String`

Exact left-to-right content; no separator, newline conversion, normalization,
encoding or automatic trailing newline. The source/native contract preserves
all Bend Char payloads; portable JS text requires Unicode scalars. Native CPU
passes raw U32 character tests; JS rejects invalid scalars. Scalar text and bytes
pass JS conformance. No GPU, Wasm or WebGPU execution claim.

Construction is O(1) structural work. Finish is O(N+K), where N is emitted
character occurrences and K expanded tree nodes, including empty fragments.
Retained builders are unchanged. Repeated finish repeats traversal.

## Bytes

`Bytes.Builder` is persistent Data, separate from the text type. Each byte is
one U32 list element in `[0,255]`; this is not a packed U8 allocation.

- `empty(limit: U32) -> Builder` (including limit zero or 4294967295)
- `fragment(limit: U32, values: List<&2,U32>) -> Result<Error,Builder>`
- `append(builder: Builder, values: List<&2,U32>) -> Result<Error,Builder>`
- `byte(builder: Builder, value: U32) -> Result<Error,Builder>`
- `compose(left: Builder, right: Builder) -> Result<Error,Builder>`
- `length(builder: Builder) -> U32`
- `limit(builder: Builder) -> U32`
- `finish(builder: Builder) -> List<&2,U32>`

`InvalidByte{value}` rejects the first examined value above 255. At each element,
value validation precedes the capacity check; `Limit{}` stops at the first valid
byte that would exceed capacity, without scanning later elements. No partial
builder escapes failure. Empty append succeeds even at capacity. Length is
checked before increment/addition, never allowed to wrap. Compose retains the
left builder's limit and fails if right.length > left.limit-left.length.
Different intermediate limits can therefore affect success under regrouping;
content is associative when all intermediate compositions fit.

Byte append validates O(fragment length); compose, length and limit do O(1)
structural work. Finish is O(N+K). Failure and success preserve retained inputs.
To reuse a Builder, destructure `Done{+b}`; Result itself is affine by default.

## Invariants and conversion boundary

Bend has no private module members. `Buffer`, tree constructors, `scan`, `guard`,
`attach`, `combine` and `emit` are low-level implementation names, not checked
constructors. Use the API above. A caller constructing Buffer directly must
establish `length = emitted byte count <= limit <= 2^32-1` and every byte <=255.
All trees are finite. Text constructors need no additional validity invariant
for native execution; JS additionally requires Unicode scalar characters.

There is no implicit text/byte conversion. A future UTF-8 encoder must validate
scalars and append the resulting bytes; WGSL remains text, Wasm encoding uses
Bytes. LEB128 and other codecs are outside this package. Runtime allocation or
stack exhaustion is a host failure, never a truncated successful result.

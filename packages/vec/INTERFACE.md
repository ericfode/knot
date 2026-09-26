# Vec dependency interface — 2026-09-26

Status: published and verified from a fresh remote cache. Hash `0xd684886d10b431b9dce6c3b2d1ef1980`.
Import `import 0xd684886d10b431b9dce6c3b2d1ef1980/main.bend as V`.
The `release.bend` entry includes the laws, proofs, model and conformance checks.
For local development: `import ./main.bend as V`. Exact receipts are in RELEASE.json.
Base-only Bend 2.0.29. All elements are `Data`; the vector itself is affine `Type`.
No client may construct or inspect the implementation's vector constructor.

```
Vec<T: Data> : Type
Error : Data = Bounds | Empty | Limit | InvalidRange
Vec.maximum() -> U32
Vec.new(-T: Data) -> Vec<T>
Vec.bounded(-T: Data, limit: U32) -> Vec<T>
Vec.length(-T: Data, v: Vec<T>) -> Vec<T> & U32
Vec.capacity(-T: Data, v: Vec<T>) -> Vec<T> & U32
Vec.limit(-T: Data, v: Vec<T>) -> Vec<T> & U32
Vec.get(-T: Data, v: Vec<T>, index: U32) -> Vec<T> & Result<Error,T>
Vec.set(-T: Data, v: Vec<T>, index: U32, value: T) -> Vec<T> & Result<Error,Unit>
Vec.swap(-T: Data, v: Vec<T>, index: U32, value: T) -> Vec<T> & Result<Error,T>
Vec.push(-T: Data, v: Vec<T>, value: T) -> Vec<T> & Result<Error,Unit>
Vec.pop(-T: Data, v: Vec<T>) -> Vec<T> & Result<Error,T>
Vec.reserve(-T: Data, v: Vec<T>, minimum: U32) -> Vec<T> & Result<Error,Unit>
Vec.slice(-T: Data, v: Vec<T>, start: U32, end: U32) -> Vec<T> & Result<Error,List<T>>
Vec.to_list(-T: Data, v: Vec<T>) -> Vec<T> & List<T>
```

Result parameters use Base's usual elided affine quantities (`Result<Error,T>`).
`swap` replaces one indexed value and returns its predecessor (Base Array convention).
`slice` copies the half-open range `[start,end)` in order; empty ranges at length are valid.
All failures return the unchanged vector. Bounds compare against logical length before
array access. Pop does not shrink capacity. Reserve takes a total minimum, not an increment.

Physical capacity starts at 1 even for empty vectors. Growth doubles capacity.
Default logical limit is 16,777,216; `bounded` clamps its requested limit to this maximum.
Rounding can put physical capacity above a non-power-of-two logical limit. Limit 0 is valid.
Requests above the effective logical limit fail with `Limit`, before arithmetic/allocation.
The policy limit is recoverable; actual host OOM is a runtime failure, not a typed result.

Get/set/swap/pop and metadata are O(1) with the pinned native array lowering.
Push is amortized O(1); growth/reserve are O(new capacity); copied slices are O(range length).
Data values may be copied; owned arrays, closures, and handles are not accepted as elements.
This deliberate scope preserves native allocation and does not claim affine-element storage.

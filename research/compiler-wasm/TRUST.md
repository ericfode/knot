# First compiler milestone: trust boundary

The compatibility and seed reference is Bend 2.0.29, commit
`574b6d39a235b539eb19a5c532993a0abb3d11ad`. Its actual main.ts, bend.ts,
comp.ts and base.bend hashes are in `receipts/trust.json`. The launcher is
`scripts/bend-reference`; the separate globally installed Bend is not used.
Bun runs the TypeScript seed. Native builds use Apple Clang; generated JS uses
Bun because this seed's file-IO support includes Bun FFI. The emitted Wasm is
validated/compiled/instantiated by Node 22.22.3 on macOS arm64.

`bun tests/compiler-wasm/trust.ts` asks the pinned seed to load and fully check
the compiler, evaluator and complete proof entry. It records every actually
loaded Bend file, foreign definition and imported implementation, together with
hashes. This is build/dependency inspection; it supplies no Knot source semantics.
The full seed checks report zero holes. Knot's own source checking is an explicit
monomorphic enum profile, not a replacement proof kernel for the whole compiler.

The compiler closure loads 14 Bend files, the evaluator 12 and the proof entry
17. Each loads the pinned Base containing 42 foreign definitions and the two
unsafe Array.fork/Array.join declarations. Those declarations are not hidden by
calling Base fully checked. No Knot implementation adds an axiom or unsafe escape,
and no accepted input program can import Base or foreign code.

The seed's generated-JS foreign-effect inventory is narrower than the full
checked Base. The compiler uses IO.args, File.open, File.read, File.close,
File.write_bytes and IO.print. The evaluator uses the same set except binary
writing. The complete proof entry is checked, not executed. There are no array,
network, subprocess, device or clock effects in these executable inventories.
Runtime error/exit handling, primitive U32/Char/Nat lowering, allocation and
closures are also trusted parts of the pinned seed's comp.ts/runtime. The foreign
list is not a complete proof or inventory of all such intrinsic lowering.

Byte emission uses the published checked API of
`0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend`, fetched by exact hash and recorded
from the actual seed cache. Its loaded SHA-256 is
`b1c672949a72bcbc37509e31a1a20715eb73813904a50157328ded9ed0069ff1`.
Its existing publication, law, boundary and fresh-consumer evidence remains in
`packages/output_builder/RELEASE.json`. Knot calls fragment, compose, empty,
length and finish; it does not construct the package's unchecked Buffer directly.
The package source and publication are unchanged.

The independent evaluator does not import the emitter, byte builder or Wasm
instruction definitions. It interprets core.Term using lexical environments and
source argument/binding frames. The emitter does not import the evaluator or
its result. They share the checked source representation and the pinned runtime;
the separate upstream interpreter and literal observations constrain that shared
front end. This is finite differential evidence, not a universal correctness proof.

The Node adapter only reads a module and invokes WebAssembly APIs/exports.
wasm2wat decodes emitted bytes for inspection and valid-mutant checks; neither it
nor an assembler participates in Knot's emission. The Python harness generates
reference call wrappers, invokes tools and compares literal results; it contains
no source-language parser, checker, evaluator or emitter.

Input/semantic failure or budget exhaustion happens before output is opened.
Host write failure may leave an incomplete file; only a successful exit plus a
new Built record and verified bytes is accepted as emission. No crash durability,
atomic replacement, arbitrary-host stack safety, general affine-resource heap,
GPU source lowering or full self-hosting follows from this milestone.

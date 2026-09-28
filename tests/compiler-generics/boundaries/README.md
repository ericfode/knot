# Generic checker boundaries

These 15 fixtures supplement the original immutable generics corpus. Their
expectations come from the pinned Bend 2.0.29 interpreter and explicit review
of Knot's supported boundary. They cover concrete disagreements found while
reviewing the new type algebra and generic checker. The original 40 fixtures
and the two supplemental fixtures remain unchanged.

`expectations.json` freezes 12 seed-valid programs, three seed rejections and
26 seed entry calls. Knot must run seven programs, reject three invalid
quantity prefixes, and report Unsupported for five unimplemented forms.
All exported test entries use nullary enums; unsupported functions still
undergo whole-book checking even when `main` does not call them.

| Cases | Fixed obligation |
| --- | --- |
| Four `meet-*` cases | `&2` is an identity and `&0` absorbs symbolic quantities before invariant datatype comparison. |
| Two `prefix-overrides-*` cases | `+Family` replaces all leading quantity arguments with `&2`, including explicitly written arguments. The seed discards an overwritten undefined name before name checking. |
| Two `prefix-forward-*` cases | `+Family` requires the preceding family declaration, even with explicit quantities. |
| `prefix-needs-quantifier` | `+Family` requires at least one leading quantity parameter. |
| Two `boxed-live-*` cases | Instantiation at `Type` or `Quant` cannot turn a live constructor field into an erased placeholder. This representation is Unsupported. |
| `type-valued-result` | Type-returning definitions remain Unsupported. |
| `monomorphic-kind` | A zero-parameter `Kind(&2)` family retains the enum host representation. |
| `value-indexed-family` | Value-indexed families remain Unsupported. |
| `constructor-local-type` | Constructor-local type binders retain the structural parser's Unsupported boundary. |

The adapter reuses the original seed-only regeneration script. It extends only
the syntactic enum-header recognizer for the literal `is Kind(&2)` header;
constructor declaration order still fixes every host tag. It does not run
Knot or infer expected results from generated Wasm.

```sh
BEND_NO_TELEMETRY=1 python3 tests/compiler-generics/boundaries/regen.py
```

The combined generics gate checks every fixture in native and Bun lanes,
evaluates every supported call, compares actual Node Wasm results, and verifies
that rejection leaves existing output artifacts untouched.

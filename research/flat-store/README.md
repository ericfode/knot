# Bend-emitted flat Wasm store

The Bend instruction builder and module emitter produce an actual 1,050-byte Wasm
module implementing init, indexed put, allocation, take and release. Both seed
backends emit the same bytes. Node executes the module against an independent
Bend list model after every operation. This is a runtime building block; the Knot
frontend and enum-only Wasm profile are unchanged.

```text
runtime.bend             assembly.bend / module.bend       actual Wasm engine
store instruction lists → checked binary encoding         → linear-memory transitions
                                                               ↓ compare
owned-store/model.bend   oracle.bend                       → every logical word
independent list states → independent word observations      and padding canary
```

## Reproduce

```sh
python3 research/flat-store/check.py
bun research/flat-store/trust.ts
```

The script uses the pinned Bend 2.0.29 seed, native and Bun builds, Node 22.22.3,
and `wasm2wat` for inspection only. No host assembler or host store implementation
participates. Outputs, exact commands and hashes are retained in
[receipts/gate.json](receipts/gate.json). Deliberate artifacts include the actual
[Wasm bytes](receipts/native.wasm) and [decoded instructions](receipts/store.wat).
Module SHA-256:
`0dfc76faa3a89c6d78f9a30e0a2c8e60de54158bf5181246e9a4106d36f4dbc4`.

## Verified boundary

- 15 filled laws, zero holes: five quantified codec/failure equations and ten
  concrete address/encoding equations. No universal transition-refinement claim.
- 3,534 instances and 13,621 status/full-state observations per emitter backend,
  including 3,510 bounded exhaustive traces and two installed near-ceiling states.
- Seven lifecycle checks and 24 literal codec/encoding observations per backend.
- Nine parseable, type-correct mutants emit valid modules, then fail unchanged
  semantic assertions. The rejected-reinit mutant detects a memory write even
  when the returned error status is correct.
- Exact two-page memory, no Wasm imports, no growth, and unused bytes preserved.
- Seed trust inventories include 42 loaded Base foreign declarations and unsafe
  Array.fork/Array.join; generated emitter/oracle/probe effects contain IO.print.

The historical first gate had an aliased-buffer assertion for rejected init.
Its receipt remains explicitly disqualified for that preservation claim. The
current gate freezes a copy and retains the distinguishing semantic mutant.

The [contract](SPEC.md) and [law review](LAW_REVIEW.md) define error precedence,
generation retirement, free-list order, payload return and privileged-memory
boundaries. The [semantic/style report](PERCH_REPORT.md) records 308 relevant
semantic checks without above-floor findings. Style remains attention: none of
106 declarations meets all three targets. These judgments are advisory.

## Integration still required

Word payloads represent owners; this module does not reclaim nested Type graphs
or keep reusable Data alive across suspended tasks, joins and device readers.
The caller still supplies a globally fresh arena ID. Snapshot cloning/restore is
unsupported. The locator utility is a three-word codec, not yet an independently
qualified twelve-byte transport. General compact field descriptors and live-field
projection remain to be integrated. This increment does not run on the GPU.

Next combine checked field layouts with these storage transitions, then lower
constructor/pattern operations and sound structural descent to real Wasm tree
programs. Qualify the GPU storage/root lifetime concurrently. Milestone 1 and the
whole self-hosting/generated-GPU goal remain open.

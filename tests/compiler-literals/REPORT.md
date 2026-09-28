# Literals executor handoff

Implemented the frozen U32/Nat/Char/String surface through bundle parsing, checked literal matrices, independent source evaluation and the new `knot-literals-wasm-1` profile. The ABI retains unary Nat cells and uses a 64 MiB arena with explicit frames/returns for the frozen 65536-depth case. Base source bodies and trusted intrinsic lowerings have separate audit categories.

The original 40 fixtures and observations are unchanged. Commit `d3c1e7b` fixed the 12 supplemental bootstrap-helper calls before implementation. See [README.md](README.md) for the exact contract and limits.

## Deterministic gates

All 16 registered gates completed with exit 0 in one serial runner invocation. The runner self-test also passed all 18 tests. Counts below are copied from the runner; categories overlap and are not summed.

| Gate | Exact counts |
| --- | --- |
| frontend | boundaries=24; fixtures=14; lane observations=28; mutants=4 |
| checker | bound observations=16; bounds=2; budgets=10; fixtures=49; lane observations=98; mutants=7 |
| structural | bounds=4; fixtures=16; lane observations=64; mutants=7 |
| fields | bound observations=12; bounds=2; budgets=36; fixtures=40; host boundaries=6; lane observations=240; mutants=9 |
| wasm | boundaries=44; execution lanes=2; fixtures=25; mutants=7; reference calls=90; rejects=64 |
| wasm-trust | entries=3; proof holes=0 |
| fields-trust | entries=4; proof holes=0 |
| structural-trust | entries=2; proof holes=0 |
| owned-store | cases=3532; execution lanes=2; literal witnesses=15; mutants=6 |
| flat-store | bun=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621); mutants=9; native=(installed boundary states=2; instances=3534; lifecycle checks=7; observations=13621) |
| recursion | fixtures=19; mutants=3 |
| fields-wasm | boundaries=30; fixtures=8; mutants=4 |
| modules | artifact preservation probes=60; byte identity pairs=21; check observations=102; compile observations=102; eval observations=118; execution lanes=2; fixtures=51; mutants=5; pin observations=22; proof entries=4; reference calls=59; tampered base observations=6; trust audits=42; wasm observations=54 |
| census | classes=40; declarations=1047; files=64 |
| lint:verify | law rules=8; tests=127 |
| literals | agree eval observations=560; agree fixtures=25; artifact preservation probes=32; boundary probes=8; byte identity pairs=25; check observations=82; compile observations=82; eval observations=592; execution lanes=2; fixtures=41; invalid fixtures=11; mutant eval observations=2; mutant wasm observations=5; no artifact probes=32; proof entries=3; proof laws=24; reference calls=287; semantic mutants=5; trust audits=50; unsupported fixtures=5; wasm observations=560 |

Receipt drift: identical=63; semantic=12; volatile-only=7. Shared receipts were left for the coordinator. Only the literal receipt is copied from this run, after checking every recorded input hash against the final working tree.

The [campaign receipt](receipts/campaign-gates.json) retains counts, source/dependency identity, drift classification and measured execution metadata. [The literal receipt](receipts/literals.json) contains every new observation.

## Fixture and mutation coverage

The original freeze has 40 books and 275 seed calls; the supplemental book adds 12. The 25 accepted books contribute 280 calls, tested in both evaluator and compiler lanes. All 11 Invalid and five Unsupported books retain their frozen outcomes; the latter retain exact prefixes. Five type-correct mutants are killed: signed compare, trapping division by zero, masked shifts, merged surrogates and a Nat offset off by one. Compiler/typecheck failures do not count as kills.

Three complete new proof entries check 24 filled laws. These prove the named arithmetic guards, literal-reading cases, source transitions, matrix expansion and the legacy capability boundary. They are not a whole-compiler or all-input intrinsic refinement proof.

## Offline preflight

units=590; files=35; unranked files=0; empty files=0; truncated units=124; truncated by limit=(caller-or-byte-limit=20; context-file-limit=44; context-helper-limit=72); supporting role impossible=125; role gap units by reason=(context-file-limit=44; context-helper-limit=72; nonlocal-import=7; truncated-context=124); max state bytes=45570; composition available=False; composition reasons=['unresolved_composition_context', 'composition_byte_limit'].

All 35 changed Bend files parsed. Every new family closes local imports and is below 48000 source bytes. Eight family compositions have complete local context; emission retains the published ByteOutput context blocker. Declaration context truncation remains, so every family reports attention. Zero provider requests were made. Compression, Delight, memetic identity, Anticipation, Payoff and Galaxy-brain ratings remain unmeasured; no live style pass is claimed.

| Family | Source bytes | Truncated units | Structural blockers | Composition context available |
| --- | ---: | ---: | ---: | --- |
| literal-frontend | 18032 | 6 | 6 | True |
| literal-primitives | 14979 | 2 | 2 | True |
| literal-types | 30652 | 14 | 14 | True |
| literal-patterns | 46105 | 23 | 23 | True |
| literal-source-machine | 37938 | 24 | 24 | True |
| literal-instruction-graph | 23473 | 16 | 16 | True |
| literal-machine-runtime | 22304 | 5 | 5 | True |
| literal-emission | 42949 | 23 | 24 | False |
| literal-algebra-laws | 21490 | 7 | 7 | True |

[The compressed preflight receipt](receipts/preflight.json.gz) retains every declaration and family result.

## Prior failures and remaining work

The first full run exposed a legacy single-file literal misclassification and a non-tail token scan on the existing 50000-blank-line module. Both were fixed in implementation; existing assertions were not changed. Census approval also required regeneration of its inventory. Later native-build failures were timeouts and transient Clang lookup failure under high host load. A controlled native build took 51.023 seconds at high load and 15.624 seconds after load fell; this is scheduling evidence, not a compiler speedup claim. The final serial run retained every existing timeout and assertion.

Coordinator work: review/merge this branch, refresh shared receipts after integration, and run live semantic/style Perch. Other emitters must account for Literal, Intrinsic and Default core variants. The next language increment still needs generics/quantity arguments and broader pattern/recursion support. Primitive/structured host observations, reclamation (R3/R7), full intrinsic refinement and self-hosting remain outside this acceptance.

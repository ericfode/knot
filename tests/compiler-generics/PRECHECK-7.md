# Current generics executor conditions

Starting head: `d4789f16`. Controls were independently frozen in `71df185d`,
before the three-line header-layout repair. All earlier fixture sources,
expectations, laws, proofs and required mutants remain unchanged. The ten
complete supplied program hashes are replayed in
[`prechecks/reported-expectations.json`](prechecks/reported-expectations.json).

## Supplied dispositions

| Fingerprints | Disposition | Concrete evidence |
| --- | --- | --- |
| `72dfd6dc31ecf19cd891` | Fixed | The seed accepts `ce3f50323140ab10`. Both datatype kind routes now skip layout before the required colon. Parse succeeds; checking reaches the independent definition-value refusal in its body. Five accepted layout controls and two omitted-colon negatives prevent overacceptance. |
| `61d4c9784682a189d345`, `5ddb3eb23c17c9de47b6`, `0f32458d73d3e58df568`, `5fee6563bd061837ffcf`, `00546995d664301756fd`, `269defa1a458be69e47f` | Disputed | Each diagnostic has exactly four TSV fields, the correct Invalid/exit-2 pair and a numeric span. `expected-:` has no tab or control character. The precheck's `[a-z0-9-]+` code restriction contradicts the stated TSV contract and the unchanged `expected-:` classification pin. The replay preserves all three Invalid outcomes at their original spans. |
| `2479f63e20371fb1bd9e`, `3243ea49e491d4a71e20`, `e7e4004ce37fce303e1b` | Disputed | The recognizer entered `Name<` before the diagnostic's `:` or `=` token. `src/SPEC.md` lists this exact prefix-only policy. The coordinator-authorized application-return-after-prefix pin and its restored mutation control require Unsupported. A diagnostic token is not the recognition boundary. All three books remain refused in check/eval/compile, preserving artifacts. |
| `c98eec3a22494b9f0201`, `47be583c3da6e599c04c` | Disputed | The adjacency check recognizes a name, then locates the detached `{`. The seed completes a bare variable and rejects the brace as a new declaration. Equal offsets therefore do not identify the same recognized prefix. Seven unchanged token-gap pins and the filled `spaced_term_token` law require Unsupported. These programs never execute or emit. A more precise detached-brace pin belongs to the coordinator's separate modules ruling. |
| `48be3d3057909f734efb` | Disputed | The seed kernel returns constructor `Nil`, arity 0, and its own renderer prints `[]`. Knot returns `Evaluated\t1\t0\tNil{}`: the same empty constructor and the unchanged classification CLI pin. `seed-value.ts` independently reproduces the raw constructor observation. String equality between different established renderers is not value inequality. The fields-profile module validates and matches between builds; no boxed address is counted as an enum value agreement. |

The final supplied condition is truncated after its ledger field. Its visible
fingerprint, source hash, seed acceptance and Knot diagnostic are sufficient to
recover the complete `ce3f...` program from the fixed generator. No additional
unseen conditions are invented.

## Mechanism and verification limits

Header layout uses the existing `S.skip_lines` at the result-arrow boundary and
the two datatype-colon boundaries. Arrow adjacency and required-colon checks
remain in force. The fixed-generator `d4746ca922b03c56` and
`f1d3c4a38ecfc3eb` programs expose the adjacent arrow/monomorphic-kind gaps and
are included in the same repair. No frontend helper was added: the original
definition census remains 48.

Three universal boundary equations have complete proofs in
`src/parse-layout-PROOF.bend`. They preserve parsing under layout at the stated
boundaries, including refusal results; they do not prove general parser
soundness, seed refinement, or the entire type/application contract. Existing
D21 obligations remain required. Three new semantic mutants restore the
demotions; additional witnesses exercise generic Kind and applied results.

Fresh focused verification builds all four CLIs in both native and Bun lanes,
replays all 32 frozen controls and kills all three new type-correct mutants in
both lanes, including four additional witness kills. Three complete proof entries
(header layout, frontend and declaration order) print `All terms check.` The
replay records 256 phase observations, 42 preserved artifacts, 22 evaluator
agreements, 18 actual Wasm value agreements, 11 byte-identical module pairs,
one seed constructor observation and four boxed module validations. Source
hashes remain unchanged throughout. Measured focused wall time is 268.490350
seconds; raw evidence stays in ignored `.local/generics/precheck-7/`.
The first attempt lacked SDKROOT and failed clang's `math.h` lookup; its log
is retained. The successful retry supplies the explicit SDK, as the gate runner
does; no source or expectation changes were made to repair that host setup.

The reading hypothesis is one existing layout primitive applied symmetrically
at header delimiters, with exact laws. Offline manifest preflight has 28 groups,
1248 units, 49 files, 28 available compositions, zero truncations/blockers and
zero provider requests. Compression, Delight, memetic identity, Anticipation
and Payoff remain unreviewed. There is no numeric score or automatic style pass.
The census has 49 files, 738 declarations and 41 classes.

The inherited C1 run compares the starting `d4789f16` against the actual campaign
base, `c0bd08d0`, rather than the previous repair commit. A committed-head replay
follows this repair. Alphabet, renderer and recognized-prefix disputes remain
explicit; the condition ledger is not modified. Helper lanes and manifest
`d4_targets` are unavailable, and codec rules do not apply. Neither that partial
review nor an offline preflight is reported as a full semantic review.

Full gate counts and measured under-load acceptance are recorded after running
`npm run -s gates`. Closures D26 reconciliation, assertion/pin rulings, shared
receipt refresh and live Perch remain coordinator actions, as specified in
`MERGE-WITH-CLOSURES.md`, `RULINGS.md` and `BOUNDARY-PINS.md`. The inherited
monomorphic checker order residual and boxed host export boundary retain their
existing owners. No merge, push, rebase or other-worktree write occurs here.

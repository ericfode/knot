# Reported C1 probes and header layout

`reported-expectations.json` freezes 19 controls under D7 before the header
repair. Ten retain the exact complete source hashes in the current user report;
two more come from the same fixed precheck generator. Five accepted controls
isolate datatype-colon and result-arrow layout, including comments and blank
lines. Two missing-colon twins remain Invalid. Earlier expectations stay fixed.

The seed parser accepts line breaks before a datatype's colon and before a
function's glued `->`. Knot must parse those headers, then check their bodies.
The reported datatype-colon program may retain its independent Unsupported
definition-value boundary. Neither layout change licenses a detached arrow or
constructor brace, or an omitted colon.

The List witness has a frozen seed constructor observation from `seed-value.ts`:
`{constructor: "Nil", arity: 0, display: "[]"}`. The seed's own renderer sugars
that empty constructor. Knot's existing classification pin is
`Evaluated\t1\t0\tNil{}`. These denote the same empty value; changing the frozen
CLI pin to satisfy a string comparison would change the established protocol.
The new replay checks the seed constructor independently and keeps that pin.

Boxed result programs are evaluated and their emitted Wasm is validated and
compared between builds. No cell address is counted as agreement with a seed
constructor ordinal. Closed enum controls retain actual Wasm value agreement.
Diagnostic shape is four tab-separated fields; the existing `expected-:` code
contains no tab or control character. Existing prefix-only type-expression and
spacing refusals remain subject to their fixed pins and `src/SPEC.md`.

The pre-repair observations are retained in ignored
`.local/generics/precheck-current/reported-before.json`. Fresh seed syntax,
checking, execution and constructor observations are in the frozen manifest.
This checkpoint adds controls only; it does not claim the layout repair passed.

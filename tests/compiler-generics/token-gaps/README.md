# Term token gaps

Frozen before the review-round-5 repair (D7). Seven seed-invalid books insert
one space inside `->` or before a constructor brace in a term or pattern;
the three forms are tested with and without generic dispatch, and the arrow
also has an applied-result-type witness. Knot must refuse them as
`Unsupported parse spacing` in check, eval and compile, preserving an old
artifact. Two seed-valid controls preserve glued terms and spaced datatype
constructor declarations; every call must agree in both lanes and Node Wasm.

Run `BEND_NO_TELEMETRY=1 python3 tests/compiler-generics/token-gaps/regen.py`.
The seed observations include source hashes, exact diagnostics and all enum
entry calls. No observation is derived from Knot.

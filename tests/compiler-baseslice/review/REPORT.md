# Baseslice review round 1

Starting head: `a7817bf89adbdbc819412af64f91d7265ad6ceb8`.

The three confirmed major findings are annotation shadowing, dotted typed-let
acceptance, and false Invalid classification of resolved function values.
`expectations.json` was frozen before production repairs. Two independent seed
freezes reproduce all 26 fixtures. Every rejected fixture reaches its intended
seed diagnostic in checking, interpreted execution and native compilation;
every accepted fixture has matching interpreted and native enum values.

The seven shadowing pairs cover result types, later parameters, erased parameters,
parameter/local/erased-local let annotations and dependent constructor fields.
Controls rename only the shadowing binder and its uses. An additional control
keeps a binder named `Flag` in its own annotation, before it enters scope.
The field control is checked/evaluated; the enum emitter remains Unsupported for
fielded declarations.

Typed-let probes retain the seed's distinction: ordinary dotted binders are
rejected as non-simple names; reusable dotted binders are rejected as malformed
promotion syntax; erased dotted binders are accepted. The latter requires a
conservative Unsupported until scope-aware binding is implemented. Simple-name
controls cover all three quantities.

Function-value probes cover a filled function and an erased forward reference.
Both are seed-valid and evaluate to `On{}`. Direct calls and local value shadowing
remain accepted. A genuinely free name stays Invalid. No existing fixture,
expectation, assertion or program budget is changed.

Reproduce the immutable seed evidence with:

```sh
export BEND_NO_TELEMETRY=1
python3 -B tests/compiler-baseslice/review/regen.py
```

Production repairs, deterministic gate results and proof limits will be recorded
in the following verified commits. Live semantic/style Perch is coordinator-only;
no rating or pass is claimed on any style axis.

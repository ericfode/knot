<!-- prechecks packet v1; rule=passages-agree; increment=generics; head=78c4942e642a; base=cc9f2fd23d59; builder=scripts/prechecks/packets@3a2ef420dff1; sources: src/SPEC.md@78c4942e sha256=ffb28602853c4926b5bfb22d557cd58212d80573be45eca5ae6a85ed557e6a20; tests/compiler-generics/README.md@78c4942e sha256=999b7380af0124c9f490763d0f76eeed8add81585d171b13ea67d5135032946f; tests/compiler-generics/README.md@78c4942e sha256=999b7380af0124c9f490763d0f76eeed8add81585d171b13ea67d5135032946f; tests/subsets/CLASSIFICATION.md@78c4942e sha256=04308147112b4dc297ad90a52decd890083d51b918c06626be8f8f175361a4eb; tests/subsets/CLASSIFICATION.md@78c4942e sha256=04308147112b4dc297ad90a52decd890083d51b918c06626be8f8f175361a4eb -->
# Claim
Term `return_type_application`. Passages this branch changed or added:

- src/SPEC.md:109 (section: Accepted language): `return_type_application` now states that `-> Name<` enters the typed-result grammar; `binding_type_application` is retired.
- tests/compiler-generics/README.md:105 (section: Review round 1): The generic parser accepts them, so six classification cases, three classification-gate mutants and the laws `return_type_application` and `binding_type_application` conflict.
- tests/compiler-generics/README.md:122 (section: Review round 1): The proposal (not committed; it changes classify-2 assertions and needs the coordinator's authorization) gives the three seed-accepted application cases phase expectations like `generic`, pins the after-prefix twins at `Unsupported parse type-expression`, retires the three classification-gate mutants with their anchors, restates `return_type_application` as the typed-result transition and retires `binding_type_application`.
- tests/subsets/CLASSIFICATION.md:158 (section: Generics supersession — 2026-09-28): Six classify-2 cases (`application-parameter`, `-return`, `-binding` and their `-after-prefix` twins), their three classification-gate mutants and the laws `return_type_application` and `binding_type_application` also conflict with generic type applications.
- tests/subsets/CLASSIFICATION.md:166 (section: Proposed classify-2 supersession (awaiting authorization)): The classification gate retires its three application mutants with their anchors; `return_type_application` is restated as the typed-result transition and `binding_type_application` is retired.

# Evidence
Other passages that mention the term:

(none)

# Scope
Only the text above is evidence. Anything not shown is missing evidence, not a pass.

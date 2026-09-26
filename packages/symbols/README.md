# Symbols

Append-only exact String interning with stable U32 IDs, checked reverse lookup,
and explicit affine table lifetime. Original code: MIT-0. Bend 2.0.29 reference.
Published: `import 0xf5507d46d06a1a8043dcb1a582194615/main.bend as S`.
See INTERFACE.md for the supported API and SPEC.md for semantics/costs.

```sh
scripts/bend-reference packages/symbols/example.bend
python3 packages/symbols/scripts/gates.py
python3 packages/symbols/scripts/benchmark.py
```

The example round-trips `compiler.λ` and returns 1. All implementation, model,
laws, test semantics and benchmark workloads are Bend. Python/JS only drive tools,
compare outputs, record hashes/timings, inspect closure, and publish.

Review LAW_REVIEW.md for operation coverage, inhabited domains, actual theorem
boundaries, hostile-caller review, mutation witnesses, and backend trust. Runtime
conformance compares full observable traces with an independent name-list model.

Publication entry is release.bend, including PROOF.bend and its laws in the actual
upload closure. Consumer API is `<hash>/main.bend`; importing `<hash>/release.bend`
also loads checked laws/proofs. Release must pin Vec's published hash first.
After inspecting Vec's RELEASE.json and remote validation, run:

```sh
python3 packages/symbols/scripts/publish.py <verified-vec-hash>
```

The script reruns gates against the hash dependency, rejects unexpected upload
files, publishes anonymously, compares expected/returned identities, and runs a
fresh-cache consumer on native CPU and JS. No GPU execution claim. STATUS.md and
RELEASE.json state whether this final step actually happened.

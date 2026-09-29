# knot-image-1 encoder gate

`src/image.bend` (with `image-plan`, `image-layout` and `image-decode`) encodes a checked core book to a
`knot-image-1` image (contract: [vm/SPEC.md](../../vm/SPEC.md)) and decodes one back. `compile-cli --profile=knot-image-1` selects it. Run the gate with

```sh
BEND_NO_TELEMETRY=1 python3 -B tests/compiler-image/check.py
BEND_NO_TELEMETRY=1 scripts/bend-reference src/image-PROOF.bend      # All terms check.
```

| File | Role |
|---|---|
| [expectations.json](expectations.json) | Frozen (D7): the explicit list of 690 sources, the reference image of each book `check-cli` accepts, the committed golden images the Bend codec must read, the profile's contract and the synthetic book. No verdict of `check-cli` is frozen |
| [seed-audit.json](seed-audit.json), [audit.py](audit.py) | The pinned seed's verdict on every source `check-cli` reports Invalid: 83 rejected, 17 D4 gaps that the seed accepts (recorded, not judged) |
| [reference.py](reference.py) | Independent reference: declarations read from source text, the core `check-cli` displays, `vm/check-spec.py`'s projection and `vm/serializer.py`'s layout |
| [freeze.py](freeze.py) | Discovers the source list and writes `expectations.json`; the gate recomputes the contract and every frozen image and requires them unchanged |
| [synthetic.py](synthetic.py) | A wide 5.2 MB book with the plan it must encode to, generated together |
| [fuzz.py](fuzz.py) | Seeded generators: small programs in the checked profile (erased and reusable fields, parameters and lets, nested matches, calls), 300 a run, each one `check-cli` accepts must encode to the reference's bytes and round-trip; and random record plans with every node form, 300 a run, which the Bend codec must read and write back as the reference does |
| [render.py](render.py), [image-cli.bend](image-cli.bend) | Two decoders' plans in one canonical text; `image-cli decode`/`recode`/`plan`/`roundtrip`/`named`/`answers` is the Bend codec driver |
| [writes.c](writes.c), [writes.js](writes.js) | Observe every write to a file: DYLD interposer (native), Bun preload (JS) |
| [witnesses/](witnesses/) | Small books for mutants: reordered arms, a let that changes type, a shared type and constructor name, nested cases, many slots |
| [LAW_REVIEW.md](LAW_REVIEW.md) | The open general round-trip law (D21) in its corrected, partial-correctness form, the counterexamples of its first statement, the twenty-eight closed laws and what each covers |
| [REPORT.md](REPORT.md) | What was built, evidence, limits, review round 1, and what the merge wave must add |

Sources: an explicit list (`expectations.json`), discovered once from every `tests/*/fixtures/**/*.bend`, the subset
corpus, `vm/golden/*.bend` and the witnesses. The gate never globs, so a merge that adds a fixture or a golden changes
nothing it judges. Of the 690, `check-cli` accepts 96 (this run's own `check-cli`, built from the tree under test): the image
of each is compared with the frozen reference byte for byte. A source that `check-cli` refuses is not held to a snapshot:
the image profile must answer with the same exit and stderr as that `check-cli`, live. A source that
`check-cli` starts to accept is judged by the live reference; a book accepted at the freeze and refused now fails the gate.
Of the Invalid sources, the seed accepts 17 (`seed-audit.json`): D4 gaps that this gate records and does not judge.

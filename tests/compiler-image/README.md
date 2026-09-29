# knot-image-1 encoder gate

`src/image.bend` (with `image-plan`, `image-layout` and `image-decode`) encodes a checked core book to a
`knot-image-1` image (contract: [vm/SPEC.md](../../vm/SPEC.md)) and decodes one back. `compile-cli --profile=knot-image-1` selects it. Run the gate with

```sh
BEND_NO_TELEMETRY=1 python3 -B tests/compiler-image/check.py
BEND_NO_TELEMETRY=1 scripts/bend-reference src/image-PROOF.bend      # All terms check.
```

| File | Role |
|---|---|
| [expectations.json](expectations.json) | Frozen before `src/image.bend` existed: the 681 frozen sources, `check-cli`'s verdict on each, the reference image of each accepted book, the profile's contract and the synthetic book |
| [reference.py](reference.py) | Independent reference: declarations read from source text, the core `check-cli` displays, `vm/check-spec.py`'s projection and `vm/serializer.py`'s layout |
| [freeze.py](freeze.py) | Writes `expectations.json`; the gate recomputes it and requires it unchanged |
| [synthetic.py](synthetic.py) | A wide 5.2 MB book with the plan it must encode to, generated together |
| [render.py](render.py), [image-cli.bend](image-cli.bend) | Two decoders' plans in one canonical text; `image-cli decode`/`recode` is the Bend codec driver |
| [writes.c](writes.c), [writes.js](writes.js) | Observe every write to a file: DYLD interposer (native), Bun preload (JS) |
| [witnesses/](witnesses/) | Small books for mutants: reordered arms, a let that changes type, a shared type and constructor name, nested cases, many slots |
| [REPORT.md](REPORT.md) | What was built, evidence, limits, and what the merge wave must add |

Sources: every `tests/*/fixtures/**/*.bend`, the subset corpus, `vm/golden/*.bend` and the witnesses. Of the
681, `check-cli` accepts 96; the image of each is compared with the reference byte for byte. The rest are
rejected or unsupported by the checker, and the image profile must answer with the same exit and stderr.

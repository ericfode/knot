# Modules fixture suite (campaign increment 4)

This suite freezes expectations for **modules and Base loading**, rung 4 of the
[compiler campaign](../../docs/COMPILER-CAMPAIGN.md). Rung 4 covers `./` and hash
imports from a frozen local bundle, and loading the pinned `base.bend`. Under
D7 every expectation was fixed before implementation. The pinned seed produced
the values, or they are literal reviews marked `knot_expected`. None comes from
Knot's output, and none may be edited to fit it. Under D4, Knot reports a form
it cannot check as `Unsupported`, never `Invalid`.

```sh
python3 tests/compiler-modules/regen.py          # verify; exits 1 on any difference
python3 tests/compiler-modules/regen.py --write  # re-record; review the diff before committing
```

## Layout

| Path | Contents |
| --- | --- |
| `fixtures/*.bend` | 40 entry programs, one feature or edge each. Each declares its own nullary result enum and a `main` the seed runs. |
| `fixtures/lib/` | Helper modules the entries import. They are not entries; the cycle helpers fail when run alone. |
| `calls/*.bend` | Committed seed wrappers for the 8 calls with arguments. The seed runs only `main`. |
| `bundle/lib/` | The frozen package store (`BEND_LIB`): ByteOutput `0xc409b77d3230ca33374caf6b0993f0cb`, the synthetic `0x4454ff15e96d17231b8b4ebd9030ac38`, and one local `names/` entry. |
| `bundle/hub/` | The offline hub stub (`BEND_HUB`). It holds only its README. |
| `expectations.json` | The frozen oracle for every fixture and call. |
| `regen.py` | The deterministic re-run and diff. |

## How the seed was run

Every call runs from the repository root with this environment:

```sh
BEND_NO_TELEMETRY=1 BEND_LIB=tests/compiler-modules/bundle/lib \
BEND_HUB=file://<ROOT>/tests/compiler-modules/bundle/hub \
bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts tests/compiler-modules/<file>
```

- All other `BEND_*` variables are cleared.
- Each call records its exact command, exit status, stdout and stderr.
- `regen.py` replaces every spelling of the repository root with `<ROOT>`, so
  absolute paths in cycle and missing-file errors survive worktree moves and
  the merge. Otherwise the comparison is exact.
- It first checks the pinned seed files (sha256 of `main.ts`, `bend.ts`,
  `comp.ts` and the unmodified `base.bend` `22eea839…`) and Bun 1.3.14.
- It then checks the fixture set in both directions, the source hashes, the
  wrapper text and the bundle, before and after the runs.
- For each accepted run it checks that stdout is exactly one constructor of the
  declared enum, with the recorded tag.

### Why the bundle is shaped this way

- **Store.** The seed resolves `0x<hash>/path` from `BEND_LIB`, the same layout
  as `~/.bend/lib`, and reads cached files **without verifying them**.
  `regen.py` therefore recomputes the seed's publish identity for each bundle
  package: the first 32 hex digits of sha256 over the sorted lines
  `sha256(file) path\n`. That identity must equal the directory name.
- **Package.** `0xc409b77d3230ca33374caf6b0993f0cb` is ByteOutput
  (`packages/releases.json`, `output_builder`), which `src/wasm.bend` itself
  imports. It is a byte-identical copy of the seed's store entry. All 12 files,
  including `LICENSE`, are needed for the hash to reproduce.
- **Synthetic package.** `0x4454ff15e96d17231b8b4ebd9030ac38` has two files and
  is never published. `mark.bend` declares an enum, and `board.bend` imports it
  through `./mark.bend`. Every ByteOutput fixture needs later-rung features, so
  this package is the in-rung proof that hash resolution works: a loader that
  refused every `0x` import would fail `hash-local-package`.
- **Hub stub.** On a store miss the seed would fetch from the hub. The stub
  makes that miss fail on a missing `manifest`, with no network request and no
  write into the store.
- **Named import.** `names/knot-fixture-bytes@0.0.0.1` is a local-only name
  pointing at the same hash. Only `named-package.bend` uses it.

## Seed semantics these fixtures pin down

- **Canonical names.** A module's namespace is its real path relative to the
  entry's directory, without `.bend` (`lib/flag`). A hash module keeps
  `0x<hash>/file`. Wrappers therefore print `../fixtures/<name>.Ctor{}`.
- **Aliases are per file.** An alias names exactly one import and is not
  re-exported (`alias-not-reexported`). It claims only dotted names: a local
  type or binder `F` coexists with alias `F` (`alias-name-reuse`), but a local
  `def F.keep` is refused (`alias-member-definition`).
- **Identity is the file.** Two aliases of one file agree. A byte-identical
  copy at another path is a different module. A diamond loads its shared
  module once.
- **Relative paths.** Paths are relative to the importing file, with or without
  `./`. Segments are plain names, uppercase hex is not a hash, and a hash
  package's own `./` imports stay inside the package.
- **Base is book-global.** Once any file imports Base, every later file sees
  Base names (`base-transitive`). The same bare spelling declared later is a
  duplicate, so load order decides (`base-after-module` accepts;
  `base-name-after-base` and `entry-shadows-base` reject). Base is imported bare.
- **Imports are a header.** Comment and blank lines may precede them, and a
  trailing `#` comment is allowed. After the first declaration, `import` is a
  reserved word.

## Coverage matrix

`†` marks a fixture that needs later-rung features (see *requires*). `*` marks
a Knot-specific expectation.

| Feature | Positive | Edge | Negative (seed rejects) |
| --- | --- | --- | --- |
| Qualified names `A.f`, `A.T`, `A.C` | qualified-names | lowercase-alias | bare-imported-constructor |
| Multiple files | transitive-chain | module-main | alias-not-reexported |
| Relative paths | nested-paths | bare-relative-path | import-dotted-filename |
| Module identity | diamond | two-aliases-one-file | distinct-identity |
| Alias collisions | same-bare-names | alias-name-reuse | duplicate-alias, alias-member-definition |
| Import-line syntax | (every positive) | import-comments | import-without-alias, import-non-bend, import-after-declaration |
| Cycles and missing files | (diamond: shared, not cyclic) | — | import-cycle, self-import, missing-module |
| `import Base` | base-bool, base-bool-pick†, base-list†, base-maybe† | base-transitive, base-after-module | base-with-alias, base-name-after-base, entry-shadows-base, no-base-loaded |
| Hash packages | hash-local-package, hash-bytes† | hash-internal-import†, named-package* | hash-uppercase, hash-absent-package |
| Foreign definitions | — | foreign-definition* | — |

The suite has 11 positive, 11 edge and 18 negative fixtures. They make 48 seed
calls: 30 accepted and 18 rejected.

## Knot obligations (`knot` in each fixture)

- **`match-seed` with empty `requires`.** Knot must load, check and run every
  call, and return the recorded constructor. An argument is an ordinal of its
  declared enum, given in `arguments` with the canonical type name. After this
  increment these 15 fixtures (21 calls) are the binding core. It includes the Base-only
  fixtures `base-bool`, `base-transitive` and `base-after-module`, whose
  reachable Base slice is the nullary `Bool` and its monomorphic functions (D2).
- **`match-seed` with `requires`.** Five fixtures reach later-rung features.
  Their seed results stay binding. Until each listed feature has landed, Knot
  may instead report `Unsupported` (exit 3), with a code of its choosing. It
  must never report `Invalid` and never return a different constructor.
  - `closures`: rung 7.
  - `fields`: rung 2.
  - `generics`: rung 6, covering erased types and quantity arguments.
  - `literals`: rung 5, covering numbers, strings and list literals.
  - `recursion`: rung 1.
- **`reject`.** For all 18 negatives Knot must report `Invalid` (exit 2) and
  emit no artifact or value. Codes are the implementer's to choose and must be
  stable. Every negative is within this rung, so `Unsupported` is wrong here.
  A module absent from the frozen bundle (`hash-absent-package`) is a
  resolution failure. Knot never fetches.
- **`knot_expected`.** The seed accepts these forms, but they are outside the
  rung. The reviewed literal expectation is an exact diagnostic prefix. It
  introduces the phase `load`, for import resolution before parsing the
  importer's body.

| Fixture | Diagnostic prefix | Justification |
| --- | --- | --- |
| named-package | `Unsupported\tload\tnamed-package\t` | `name@version` is a mutable hub pointer, not content identity. The frozen bundle admits only `0x` hash imports, so Knot reports the form before reading any package file. |
| foreign-definition | `Unsupported\tcheck\tforeign-definition\t` | Foreign code is excluded (`src/SPEC.md`), and D4 forbids passing it through. Parse must accept the form because pinned Base has foreign definitions. The user's definition is reported when declarations are checked, even though `main` never calls it, and before its `IO` signature is examined. |

## What the implementer wires (the gate runner is theirs)

1. **Inputs.** Give Knot the entry fixture, `bundle/lib` as the only package
   root, and the pinned `base.bend` from the seed tree. Knot must never
   contact a hub or read `~/.bend`.
2. **Calls.** For every call, invoke `export` directly with the argument
   ordinals. Compare the result tag with `tag` for the evaluator and the Wasm
   lanes. The files in `calls/` exist only for the seed. Every recorded export
   is declared in the entry file. The suite does not constrain how Knot names
   or exports imported functions in Wasm.
3. **Negatives and Knot-specific cases.** Assert the exit status and outcome
   class. For `knot_expected`, also assert the exact diagnostic prefix. A
   rejected compilation must leave any existing output file untouched, as in
   the earlier gates.
4. **Pins.** Run `regen.py` in the gate, so drift in the seed, Bun, the bundle
   or a fixture fails before Knot is compared. Never run `--write` to make
   Knot pass.

## Regenerating

`--write` rewrites only seed observations: commands, exits, stdout, stderr,
wrapper text, source hashes, bundle hashes, and constructors and tags parsed
from stdout. Kinds, result enums, `requires`, obligations and `knot_expected`
are hand-reviewed and preserved. It writes nothing when a pin, the bundle, the
fixture set or a reviewed contract fails. A contract failure is an accepted
negative, or a constructor outside the declared enum. Read the whole diff before committing. That
reading is the literal review this suite depends on. Adding a fixture means
adding its reviewed entry to `expectations.json` first. `regen.py` fails on
entries missing in either direction.

## Deliberately not covered

- Absolute-path imports: no portable expectation exists.
- Symlinked modules and case-insensitive path aliases: platform-dependent.
- `--publish`, `--checkup`, HTML bundles and the `PROOF.bend` CLI rule.
- Laws filled across modules.
- A tampered store: the seed trusts cached store bytes, so no seed oracle
  exists. The suite's own bundle check guards the frozen copy.

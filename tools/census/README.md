# Offline compiler census

```sh
export BEND_NO_TELEMETRY=1
npm run census
npm run census:check
npm run census:test
npm run census:meter
```

The [contract](SPEC.md) fixes the observations and scope. The
[generated inventories](../../docs/compiler-campaign/inventory/README.md) keep
implementation syntax, accepted input and host requirements separate.

`census.mjs` resolves local modules using the vendored parser and its original
declaration observer. Import headers use the same parser adapter as Perch.
`features.mjs` classifies original bodies, signatures and patterns before match
lowering. It records lambda captures by binder identity, rather than searching
source text for arrows or names. Offsets use the parser's UTF-16 convention;
line ranges are one-based. Law declarations and their fills are separate events;
the unique declaration count merges their resolved identities.

All `src/*.bend` files are included. Candidate packages include the six published
runtime entries plus ByteOutput, and their local/hash dependency closures. Working
package files and published imports are separate identities. A hash import must
match its release record; changed working bytes fall back to the seed's existing
local cache (`BEND_LIB`, otherwise `~/.bend/lib`). Cache misses fail without a
fetch. Package proof entries and test harnesses are outside the candidate runtime
scope. No environment file is read.

The module loader's authorized path-identity query has a `foreign` exception
pinned to `src/path-host.bend` and its exact SHA-256 in `approved.json`. Ordinary
`census:approve` does not grant or refresh that exception. Four literal policy
controls retain the default ban, the wrapper's exact bytes, file boundary and
other forbidden features. The exception covers the Bend wrapper only: the bytes
of the C/JS adapters it runs (`src/host/path-identity.{c,js}`) are pinned by the
modules gate against `tests/compiler-modules/host-check-expectations.json` and
the io-abi-2 reference bodies, with literal drift controls. The adapters are
host metadata queries; compiler semantics remain in Bend.

`approved.json` is the review boundary. Both generation and `--check` reject new
classes per declaration, new source files and new imports. They also reject arrays,
foreign definitions, holes, floating literals, unsafe declarations, parallel binds
and GPU offload in the compiler's non-Base dependency closure. Base is separately
inventoried. Neither command rewrites approvals. After an intentional profile
extension, review the policy diff, regenerate the five manifests, then run checks.
`--check` additionally rejects any stale manifest, even when source edits add no
new class. A renamed declaration requires its own reviewed approval.
`npm run census:approve` extends `approved.json` from the current inventory and
prints what it added (new files and declarations, widened classes, imports).
That printed summary and the policy diff are the review; it never lifts a
forbidden dependency feature.

The seed's hash-pinned `OPERATIONS` table and `tpl_ops` helper are evaluated in
an empty VM context, with no filesystem, process or network binding. This retains
computed operation names and JS/native differences. `WORDS` supplies the separate
numeric representation cut. No compiler or program is executed by the census.
Node 22's TypeScript stripping emits an experimental-API warning on stderr; it
does not enter the manifests.

The closure is a conservative source dependency inventory. It retains all branches,
callbacks and template value arguments. It does not specialize templates, solve
higher-order flow, remove dead code or prove type correctness. Calls through
variables are listed explicitly; their erased arguments can be over-approximated.
The uncut static closure preserves proof/type dependencies instead of hiding them
behind the runtime cut. The complete loaded Base trust inventory lists foreign,
unsafe and bodiless declarations separately from reachable operations.

The accepted inventory discovers the literal `GATES` registry without importing
or executing it, all existing adapter directories and all `tests/compiler-*`
directories. Only a suite's mapped gate, invoking a program in that suite's
directory, admits its fixtures as evidence. A trust gate in the same directory
does not qualify the suite. Positive evidence is scoped to parsing, catalog
inspection, checking, evaluation and executed Wasm. A class absent from positives
has **no positive fixture evidence**, which is not a claim that every use is
unsupported. Exact negative diagnostics stay attached to their fixtures. Gate
program, registry, manifest and fixture dependency hashes are recorded;
regeneration does not claim to have run those gates. Unknown suites/formats are
listed in `accepted.json.reports` and on stderr, with zero contributed evidence.
Registered commands without a fixture manifest remain in the discovery inventory.

`evidence.mjs` owns the small adapter table. Adding a suite requires a reviewed
path/format/gate entry and literal controls; similar JSON field names never
authorize an unknown suite. Additional manifests at a known path are reported too.

| Suite directory under `tests/` | Registered gate | Manifest(s) | Frozen stage source |
|---|---|---|---|
| `subsets` | `frontend` | `frontend-cases.json` | `tree` supplies parse evidence |
| `compiler-checker` | `checker` | `cases.json` | `knot.exit` supplies check |
| `compiler-structural` | `structural` | `cases.json` | `catalog` and `compiler`; compilation is retained separately |
| `compiler-fields`, `compiler-recursion` | `fields`, `recursion` respectively | `cases.json` | Independent `check`, `eval`, `compile` outcomes |
| `compiler-wasm` | `wasm` | `cases.json` | Gate's fixed successful `calls`: check/eval/Wasm |
| `compiler-fields-wasm` | `fields-wasm` | Both | `cases` joined to frozen `observations`; evaluator exhaustion and arena overflow stay failures |
| `compiler-nest` | `nest` | `expectations.json` | `knot.exit`, `observed.main` and `observed.calls` |
| `compiler-modules` | `modules` | `expectations.json` | `knot.obligation`, `knot_expected`, `calls`; local/hash bundle pins |
| `compiler-literals` | `literals` | `expectations.json` | `knot` or `knot_expected`, and `calls[].seed` |
| `compiler-generics`, `compiler-closures`, `compiler-baseslice` | `generics`, `closures`, `baseslice` respectively | `expectations.json` | `knot.require`, joined to `observations.fixtures` |

Future suite adapters are ready for their reviewed branch formats; only files
present in this checkout contribute to its inventory. Recognized suites without
their mapped gate live in `accepted.json.requirements`, with separate suites,
fixtures and class-to-fixture lists. Their unconditional agreement is a frozen
requirement until the gate is registered. `agree-or-unsupported` and unpinned rejection are `Unfixed`
with their allowed alternatives retained. Seed success cannot turn a frozen
Knot Unsupported result into success. No success is inferred for earlier stages
that the manifest does not separately establish. `compile` never supplies Wasm
execution evidence.

The module-fixture loader accepts bare-relative imports and verifies every
local source and hash-package dependency against that suite's frozen manifest.
It never falls back to the user's package cache for fixture bundle bytes.

`meter.mjs` compares the JS runtime/type closures against check and Wasm fixture
classes. It reports evidenced counts and inclusive coverage by evidence plus
frozen ungated requirements. The second count is planned class coverage; it
cannot establish implemented behavior. `selfhost.json.requirements` lists each
ungated suite and every class's positive frozen fixtures at each stage.
`selfhost.json` records unique declarations from non-law/proof files, compiler/package/Base
counts, ranked missing classes, every declaration's gaps and excluded law/proof
identities. File import classes apply to each declaration in that file. Each
declaration is measured independently; a caller does not inherit its callee's
feature gaps. Filled laws that implement runtime Base functions stay counted;
law and fill features merge under one resolved identity. Intrinsic/foreign boundaries remain visible. The three input
manifests are linked by SHA-256.

`census:meter` computes a read-only summary of the current tree. `census` writes
the full manifest, and `census:check` rejects stale bytes. Coverage of coarse
classes does not qualify their composition, a host ABI or a complete bootstrap.

Tests use literal-reviewed fixtures, synthetic source additions and eight
syntax-valid semantic JavaScript mutants: omitted lambda detection, ignored import
approval, bypassed intrinsic cut, conflated Unsupported/Invalid, failed fixture
admission, unknown-suite admission, counting law-file code in the meter and
admitting an ungated requirement as evidence. `fixtures/requirements.json`
fixes the evidence/requirement separation and inclusive meter counts. The three Bend
fixtures pass the complete pinned seed checker, including the filled law in
`features.bend`. They introduce no new Knot source capability.

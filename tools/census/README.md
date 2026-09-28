# Offline compiler census

```sh
export BEND_NO_TELEMETRY=1
npm run census
npm run census:check
npm run census:test
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

`approved.json` is the review boundary. Both generation and `--check` reject new
classes per declaration, new source files and new imports. They also reject arrays,
foreign definitions, holes, floating literals, unsafe declarations, parallel binds
and GPU offload in the compiler's non-Base dependency closure. Base is separately
inventoried. Neither command rewrites approvals. After an intentional profile
extension, review the policy diff, regenerate the four manifests, then run checks.
`--check` additionally rejects any stale manifest, even when source edits add no
new class. A renamed declaration requires its own reviewed approval.

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

The accepted inventory reads 144 fixed cases in five existing gate manifests
(113 distinct files). Its positive feature evidence is scoped to parsing, catalog
inspection, checking, evaluation and executed Wasm. A class absent from positives
has **no positive fixture evidence**, which is not a claim that every use is
unsupported. Exact negative diagnostics stay attached to their fixtures. Gate
program hashes are recorded; regeneration does not claim to have run those gates.

Tests use literal-reviewed fixtures, synthetic source additions and four
syntax-valid semantic JavaScript mutants: omitted lambda detection, ignored import
approval, bypassed intrinsic cut and conflated Unsupported/Invalid. The three Bend
fixtures pass the complete pinned seed checker, including the filled law in
`features.bend`. They introduce no new Knot source capability.

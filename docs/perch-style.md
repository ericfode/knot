# Style quality checks

The target is a distinctive code aesthetic: **Maximally big brain**,
**Delightful to read — high dopamine**, and **Highly memetic**. Every existing
parsed declaration is assessed against all three; an alternative implementation
is not required. Rankings are a secondary view of those independent ratings.

Version 8 is **calibrated against the user's blind taste anchors**. In two
blind rounds the user rated behavior-identical renderings. The winning style
was an "algebra register": one core idea, laws stated in notation, a checked
proof beside the code, and terse exact names. Invented vocabulary, riddles and
puzzles, narration, ornament and cryptic density all lost. v6 agreed with only
52% of those preferences, and it scored the rejected ornamental and mythic
styles highest on memetic identity.

The user asked for the rules to be updated "so that jev picks the same
stuff", and v8 does this in three ways:

- **Memetic** is now the imitable shape of the mechanism, what a fluent reader
  would copy into new code. Costume (a sustained borrowed world of names that
  must be translated back), ornament and narration earn nothing.
- **Anticipation** comes from the stated contract: types, operation names and
  compact laws.
- **Payoff** is code that visibly realizes that contract, most strongly
  through a checked proof.

Composition questions now carry per-axis wording
(`style_role.composition_axis_instructions`).

Targets, thresholds, roles and potential are unchanged. Three candidates were
drafted from two development tasks only. The one chosen by a pre-registered
rule then passed a held-out check on two unseen tasks:

- 7.5 of 9 duels, against 3.5 for v6;
- 84% of preference pairs, against 52%.

Across everything it agrees with 91% of the user's preferences. Evidence and
limits are in [style-v8-2026-09-27](perch-calibration/style-v8-2026-09-27/README.md).
It supersedes v6's clause that vacuous or decorative form can be highly
memetic.

Version 6 separated **memetic appeal from conceptual value**. A vacuous,
nonsensical, decorative or incorrect expression can be highly memetic. Its
conceptual compression, other reading qualities and correctness are independent
judgments; a high memetic score cannot compensate for a failure on those axes.
This follows the user's judgment of the [prose control](perch-calibration/memetic-prose-2026-09-27/README.md).
The [v5/v6 comparison](perch-calibration/memetic-value-v6-2026-09-27/README.md)
retains that exposed human example and fresh prose controls. Earlier receipts
keep their original rubric meaning and cannot qualify changed requests.

Version 5 separated **expressive role** from contract importance. Supporting
helpers should reinforce the main mechanism's identity and prepare the reader
for their bounded contribution. They need no independent hook or dramatic arc.
Leading declarations and the complete mechanism retain the stronger requirements.
Version 4 introduced source-blind **potential profundity**, making Galaxy brain
a conditional requirement of the combined mechanism. Missing or uncertain
relevance leaves it advisory. Version 3 introduced the
[research-informed refinements](perch-memetic-criteria-proposal.md) and separate
**Anticipation** and **Payoff** scales.
The [research on ideas generally](memetic-ideas-research-2026-09-26.md) motivates
these taste criteria; it does not validate the model's judgments. Existing
receipts retain their original rubric identity and meaning.

| Axis | Desired experience |
| --- | --- |
| Maximally big brain | A small expressive algebra or representation absorbs cases and exposes invariants. Each abstraction explains more than it adds. |
| Delightful to read — high dopamine | Exact names, rhythmic layout, symmetry and dense composition create repeated satisfying moments where the structure clicks. |
| Highly memetic | The mechanism has a shape you would copy into new code and extend: a representation, a small family of primitives with stated laws, an aligned case table, a law checked by its proof, or a recurrence. |

Memetic identity, since v8, is the pull to imitate the mechanism itself. A
recognizable shape that reuse would keep counts. Surface that reuse would strip
away does not count, and it lowers the score when it hides the shape. Such
surface includes costume names from a borrowed world, incantatory or ornamental
comments, banners, narration, puzzles and teasers. Crushed abbreviation that
hides the shape also lowers it. A figurative word read directly as the name of
one type or operation, or a coined term for a new concept, is vocabulary, not
costume. Judge the actual form rather than source self-praise. This describes
the user's calibrated preference, not a measured psychological or social
effect.

Terse notation, learned idioms and dense composition are welcome. Simple helpers
can qualify through one fitting operation or resonant expression; adding layers
solely to look clever would work against the goal. Correctness, quantity, proofs,
backend behavior and performance remain independent deterministic gates.

## Run it

```sh
# Rate each existing declaration in a file. No competitor needed.
npm run lint:style -- --live src/scope.bend

# Rate one parsed declaration, including datatypes.
npm run lint:style -- --live src/scope.bend::alternatives
npm run lint:style -- --live src/scope.bend::Scope

# Inventory project declarations; qualify bounded mechanisms separately.
npm run lint:style -- --live --all --output=.local/style-project.json

# Offline structural preflight: no credentials, .env, cache or provider request.
npm run lint:style -- --preflight --task=src/SPEC.md src/driver.bend
npm run lint:style -- --preflight --all --output=.local/style-preflight.json

# Qualify the named compiler mechanisms, each with its own composition.
npm run lint:style -- --live --manifest=docs/compiler-campaign/manifest.json
npm run lint:style -- --live --manifest=docs/compiler-campaign/manifest.json --group=checking
npm run lint:style -- --preflight --manifest=docs/compiler-campaign/manifest.json
```

### Structural preflight

`--preflight` prepares the same declaration states, contexts and composition
groups as a live run, without building request bodies, then reports what can
never pass whatever the ratings. A
truncated context withholds Anticipation and Payoff, so that unit cannot pass.
A context with unresolved non-builtin references, or a truncated one, keeps the
declaration at the leading targets, because it cannot establish the supporting
exemption. An unavailable required composition prevents qualification. With `--all` it
lists unranked files and, like a live project run, reports the composition as
unavailable (`explicit_selected_group_required`); each file is also reported as
a single-file group to help plan explicit groups. It makes zero
provider requests, writes no usage receipt and exits 3 when a structural
blocker exists. Run it before paying for a review, and after any context,
parser or scope change, to measure what the change unblocks. Its counts are
structure, not taste.

### Named mechanisms

`--manifest=FILE` reviews an ordered collection of explicit selected groups.
`--group=NAME` restricts either live review or preflight to one named group.
The manifest is JSON; all paths are relative to the workspace root, including
when the manifest lives under `docs/`:

```json
{
  "schema": 1,
  "groups": [
    {
      "name": "frontend-lexing",
      "files": ["src/syntax.bend", "src/lex.bend"],
      "task": "src/SPEC.md",
      "notes": "Character budgets, token spans and tokenization."
    }
  ]
}
```

Names are unique; each group lists distinct whole Bend files in reading order.
`task` is an optional fixed task/contract path. `notes` is optional receipt
metadata and is never sent as a rating instruction. Empty groups, duplicate
paths (including aliases), escaped workspace paths and unknown fields/options
are rejected. `--all`, positional targets and run-wide task/cohort overrides
cannot be combined with a manifest. The compiler manifest includes each
mechanism's full local import closure; a test checks coverage of every current
`src/*.bend` file and every local import, including earlier proof entries.

Every selected group gets the same declaration review and composition targets
as explicit file targets. Without a context policy, listed files come first in
their stated order, followed by known complete collaborators in lexical order.
This legacy policy preserves historical requests and their fixed controls.
Shared declarations are obligations in each selecting group with that group's
contract; the unit count includes those repetitions.

#### Interface context rule (`interfaces-v1`)

The compiler manifest sets top-level `"context": "interfaces-v1"`. This changes
context assembly, **not rubric v8 or any target**. In this policy, `files` is
the closed local dependency inventory. An optional group `selected_files`
lists the whole sources reviewed in full, in reading order; absent means all
`files`. It must be a nonempty, distinct subset of `files`. Every inventory
file must be selected in full in at least one manifest group. Runtime validation
and the compiler-manifest controls retain total source coverage and each
group's local import closure. A group filter cannot establish full coverage.

The seven oversized or downstream families now select their own mechanism
explicitly; their previous inventories remain intact. Earlier proof entries
and other collaborators are interfaces unless selected. Each selected source
appears byte-for-byte in full. Other files enter in lexical order with their
full-file SHA-256, import aliases, complete datatype declarations, and referenced
`def`/`law` signatures. Signature references are closed transitively. Law
statements are types/contracts; proof fills contribute heads without proof
bodies, with their matching law statement resolved separately. An unused proof
entry retains its imports and hash even when none of its heads is required.
Every omitted implementation is marked `interface-only` / `body omitted`.
The judge must not infer implementations or proof execution from these heads.
The legacy composition instruction, including its prohibition on inferring a
potential verdict, previous scores or missing implementation, is retained
verbatim before this interface warning. Definition heads end at the offset
reported by the parser after consuming the body colon, not a separate lexer.

Composition bytes count the UTF-8 text actually supplied: all complete selected
sources plus interface text, including its markers and hashes. The bound stays
**48,000 bytes**. Equal fits; larger is unavailable with
`composition_byte_limit`, and no selected source is shortened. Metadata and
the task are not source bytes. Declaration states also retain the independent
60,000-byte encoded-state bound, including task and metadata.

Datatype contexts follow referenced datatypes through the transitive import
closure, with cycle detection and the existing source-byte budget. File-count
and helper-count limits do not cut this type closure. Declaration contexts keep
up to 48 helper bodies and four caller bodies. Overflow uses marked signatures;
their type dependencies are still followed. Byte pressure or encoded-state
pressure may also replace a helper/caller body by a signature. Receipts classify
these as `context-helper-interface`, `context-caller-interface`,
`context-byte-interface` or `context-state-interface`, separately from missing
context; a collaborator cut to its name is `context-state-names-only`, below.
Required text that cannot fit retains `context-byte-limit` and a
truncation marker; qualification is withheld as before.

**Names-only tier (encoded-state pressure).** Both caps stay as they are: 60,000
bytes for the encoded state, task and metadata included, and 48,000 for
composition source. When every helper and caller is already an interface summary
and the state is still over 60,000, the fitting takes one more step instead of
failing. A collaborator entry, an interface summary or a body that the interface
tier kept because its interface was no smaller, becomes
`{path, name, representation: "names-only"}`: lines, text and signature are
dropped. The signature is the interface text, so it is not shortened. For
`check.bend::run` on `campaign/literals-integ`, 103 of 105 interfaces are one
line, and keeping only the first line saves 337 of 13,357 bytes, far too little.

- **Order.** Each tier takes the largest saving first, then path, then name. The
  interface tier's saving is the source bytes it removes. The names tier's saving
  is the exact drop in encoded bytes, and a cut that cannot shrink the state is
  skipped after installing the first cut's shared warning. Savings include
  source-byte and marker-count digits and summary-array commas, and are
  recomputed after each cut. The order of `calls` and `called_by` never changes the choice, and the
  names tier compares path and name by code point, so the process locale does not
  either, including supplementary Unicode scalars. On entry to the names tier,
  summary rows are also sorted by path and name; their earlier insertion order
  cannot change the complete state hash. Both earlier fitting returns and the
  interface tier's tie-break are unchanged. Fitting stops at the first
  state that fits, so an entry the cap does not need is left as it was.
- **Record and marker.** Each cut has one `summarized` row with reason
  `context-state-names-only` (an interface entry's row changes its reason; a kept
  body gets a new row), so the row count stays one per summarized declaration. The
  judge-visible `context_notes` gains `names_only: {count, note}` beside each
  entry's own `representation`, saying which context was cut to names and not to
  infer types, contracts or behavior from them. `source_bytes` falls by the text
  removed, and the files behind the names stay hash-pinned in the provenance.
- **Inert when unused.** No marker and no row change exist for a state that fits,
  so every such state is byte-identical to what it was. Over the compiler
  manifest, all 957 declaration states and 17 composition states have the same
  hashes as before, and the official preflight receipt is byte-identical.
- **Required minimum.** Primary source and task/cohort text are never shortened.
  If collaborator cuts do not suffice, compact duplicate audit rows and source
  locations first, preserving complete datatype and law text. The full metadata
  remains in `provenance.state_metadata`, pinned by a judge-visible digest.
  Only if contract text still cannot fit may it become marked names-only entries.
  Preserve the complete omitted entries in `provenance.omitted_contracts`, file
  hashes and summary rows; add `context-state-contract-limit` and set `truncated`
  in both provenance and state. That missing type/law evidence withholds
  qualification and the supporting-role exemption. Detailed audit/import
  metadata may be retained only in provenance to reach the complete names
  minimum; its omission is explicit and its digest participates in state identity.
  Throw `Style context too large after names-only summaries` only when complete
  primary, task, all context names and mandatory cut markers exceed the cap.
  The error reports that minimum and its encoded byte breakdown.
- **Advisory.** Helper/caller cuts alone set neither `truncated` nor a role-context gap, so the ordinary tier is
  never a structural blocker and never changes the role exemption. How the judge
  rates a declaration whose collaborators are only names is not calibrated. Read a
  rating whose receipt lists `context-state-names-only` rows as advisory evidence,
  not as a settled qualification, and keep the tier advisory until it is measured.

Hash imports resolve **offline** from the repository's `packages/`, followed by
`--package-store=DIR` if supplied, otherwise `BEND_LIB` if set, otherwise
`~/.bend/lib`, matching the seed's default. A store may contain hash-named directories with
complete package members, or package directories whose `RELEASE.json` has a
`closure` inventory of paths and SHA-256 digests. The resolver hashes actual
member bytes, sorts `sha256(file) path\n` by path, hashes the concatenation and
requires the first 32 hex digits to match the imported identity. All members,
including unused ones and licenses, are verified. Traversal, symlinks, duplicate
members, environment-file members and imports outside verified membership are
rejected. Failure reasons remain unresolved; no network or package installation
is performed. Every verified member participates in freshness checks. Release
metadata locates a candidate; verified member bytes establish its identity.
Headers, representations, file lists, provenance and all request hashes use
`0x<hash>/<member>`. Filesystem locations stay inside the local snapshot reader;
moving the store or checkout does not change review bytes or request identity.
Bare relative imports participate in local manifest closure. Other hash lengths
remain explicit `unsupported-package-identity`, and named/absolute imports
remain unresolved.

The current repository OutputBuilder source has advanced past its publication.
Its `bytes.bend` correctly fails the published digest. The default installed
store supplies the unmodified local release only after verification:

```sh
BEND_NO_TELEMETRY=1 node scripts/perch-style.mjs --preflight \
  --manifest=docs/compiler-campaign/manifest.json \
  --output=.local/compiler-context.json.gz
# Same context policy on a bounded explicit target:
BEND_NO_TELEMETRY=1 node scripts/perch-style.mjs --preflight \
  --context=interfaces-v1 src/core.bend
```

Without any verified candidate the published dependency stays unresolved; the resolver
does not reinterpret current package source as the old release. Other style
invocations keep legacy assembly unless `--context=interfaces-v1` is explicit.
The [context contract and controls](../tests/perch-context/CONTRACT.md) qualify
assembly only. Live ratings and semantic acceptance remain separate.

All selected groups prepare against one source snapshot before the first
provider request. Live groups run in manifest order, retaining `--jobs` concurrency
within a group. Provider failure stops later groups and saves completed/partial
evidence in one aggregate usage receipt. `--output`, compressed JSON, `--reuse`,
`--incremental` and `--fresh` work as in explicit-target mode. Exact request
identity governs reuse; changing reading order invalidates the composition
request without invalidating unchanged declaration requests.

The JSON report contains `groups`, an overall `summary`, input hashes and final
source/task/manifest/rubric freshness. Live qualification requires every selected
group's declarations and composition, one resolved model identity, and unchanged
inputs. `qualification.fully_qualified` covers the selection;
`qualification.manifest_fully_qualified` additionally requires an unfiltered run.
A group filter cannot establish whole-manifest success. Preflight reports
per-group truncation, role gaps and composition availability; exit 3 means
structural blockers, never a rating. Exit 1 denotes a failed/incomplete live run
or invalid invocation; live exit 3 denotes attention; live exit 0 means the
selected style obligations met their targets, still advisory to semantic gates.

The [compiler baseline](compiler-campaign/perch-baseline.md) retains the original
blockers and the new offline before/after receipt. It is not a Perch pass.

`lint:rank` remains an alias. `--task=SPEC.md` supplies a fixed task contract;
`--cohort='purpose or contract'` is an inline alternative. Without either, ordinary
declaration targets still apply and Galaxy relevance remains explicitly advisory.
The explicit source group is also judged as a complete mechanism on memetic
identity, Anticipation and Payoff, even without a task file.
`--json` prints the structured report. An output path ending in `.gz` saves the
same JSON losslessly compressed; `--reuse` accepts either form. `--jobs=N` sets
provider concurrency from 1 to 256. Both project mode and explicit targets
default to 16 workers, shared with semantic review. An exported `PERCH_JOBS`
overrides that default; an explicit `--jobs` overrides the environment. The
maximum inventory size is 5,000 declarations by default; exceeding it fails
preflight rather than silently truncating coverage. No automatic request retries
are made. A provider error, including HTTP 429, stops new dispatch and drains
already active requests before saving the failed receipt. Rows and retained
completed answers stay in selection order even when responses arrive out of order.

`--all` discovers tracked and nonignored new `.bend` files using Git. It includes
compiler code, packages, research, laws, proofs, fixtures and retained experiments.
Ignored dependencies, caches and build directories are not project source. Exact
parser spans identify definitions, law declarations/fills and datatypes. Files
that cannot be parsed or supplied with valid context are listed in
`inventory.unranked`; files without any supported declaration are listed separately.
An incomplete run cannot claim that everything was rated.
Project mode has no explicit bounded composition group, so `--all` returns
attention rather than a full style qualification even if all declarations meet
their targets. Follow it with explicit file groups for the mechanisms being
qualified; the command does not invent a whole-project composition score.

Function/law context uses the same pinned Bend parser and bounded working-copy
helpers as normal Perch checks. Parsed datatype references resolve locally and
through explicit relative imports, including aliases, generic type arguments and
transitive referenced types, within the existing helper/file/byte limits.
Under the legacy policy, direct datatype targets retain their one-file,
four-caller and 48 KB limits:
sibling datatypes and same-file users are included, while required external
dependencies report an explicit file-cap failure. Explicit composition groups
check datatype dependencies against their selected files within the existing
48 KB bound. Every target retains source and context hashes, truncation markers
and unresolved references. Missing dependencies and cap failures remain visible;
syntax parsing does not establish typing or dependency completeness. See the
[datatype-context repair evidence](perch-execution/role-v5-2026-09-27/datatype-context/README.md).

Each invocation shares one source snapshot across targets and their explicit
local imports. The snapshot reads and parses each real source file at most once,
including when several targets import it. Import paths, workspace and
symlink boundaries, per-declaration context limits and provenance remain intact.
Project discovery overlaps up to 32 independent file preflights and assembles
their results in discovery order. Every selected context finishes preflight
before any provider request. The next invocation reads a fresh snapshot.

Source freshness checks independently reread current bytes before requests and
again afterward. Changes
during review are reported; the ratings still refer to the recorded snapshot.
An existing output file is rejected before paid requests. Every dispatched run
also writes a secret-free local receipt under `.perch/usage/`.

Receipts record the configured `concurrency`, observed `provider_peak_in_flight`
and `preflight_snapshot` counts. `parse_calls` counts parser invocations, including
rejected syntax; it does not imply successful coverage. The `timings` object
separates preflight, explicit reuse, evaluation, final source verification and
report aggregation. Its `total_ms` includes preflight and rankings, and excludes
JSON serialization, receipt writes and output. The existing `elapsed_ms` retains
its historical scope: after preflight through assessment, before rankings.

`--incremental` automatically retains and reuses answers under ignored
`.perch/`. Use `--live --all --incremental` for the current project inventory or
select explicit files/declarations as usual. Every run prepares current source
and helper context, then only unmatched requests reach the provider. An
unrelated same-file change need not discard an unchanged declaration's rating.
Reused rows contain current source/context provenance and retain the original
answer provenance separately. Deleted or renamed declarations do not survive as
current coverage. Low, uncertain and unavailable ratings retain their status.

`--fresh` bypasses answer reuse and refreshes the automatic cache. Choose one of
`--incremental`, `--fresh`, or `--reuse`; contradictory modes fail before review.
Automatic cache identity includes the exact request, rubric, parser/context
contract, configured model and endpoint. Corrupt entries are misses. Fresh,
validated completed answers can survive a provider interruption; changed source
or model inconsistency prevents automatic cache writes.

An unchanged cached run makes zero provider requests. A moving requested model
alias may have changed upstream; cached model IDs are recorded as unverified
this invocation. Use `--fresh` when new inference or alias resolution is needed.
If fresh responses conflict with reused model IDs, the run fails visibly rather
than combining incompatible ratings. Explicit receipts predating endpoint
identity are not silently imported into the automatic cache.

`--reuse=path/to/earlier.json` reuses only rows with matching target source,
request-state, context, parser, rubric and requested-model identities. Reused and
fresh rows must resolve to one model. Completed answers from a failed run are
retained for explicit reuse; a provider failure itself yields no partial rankings
or assessments. This allows recovery without paying again for unchanged answers.

## Interpret the result

[perch-style.json](../perch-style.json) contains three primary rubrics and two
separate reading-experience scales. Big brain runs from 0 to 5; the other four
run from 0 to 4. Functions, laws, proofs and datatypes receive these five typed
Score questions plus separate binary `criticality` and `style_role` Scores in the
same request. Known truncation withholds the two reading-experience questions,
leaving five questions and explicit unavailable ratings. Criticality remains
visible but no longer selects style targets. Potential profundity is rated from the
explicit task, before the provider receives any implementation. Each declaration receives its own distributions, independent
of other candidates or their order.

The memetic ladder is **Unformed → Ordinary → Recognizable → Contagious →
Generative grammar**. Since v8, level 3 requires a distinctive, compact
mechanical pattern that a reader would copy into new code: a representation, a
set of combinators, a law with its proof or a recurrence shape. Themed names or
decoration alone never qualify. Level 4 requires a small vocabulary of
operations, with any stated laws, from which further operations visibly follow.
Popularity, actual sharing and an existing community require separate social
evidence.

| Level | Anticipation | Payoff |
| --- | --- | --- |
| 0 | Disoriented | Unresolved |
| 1 | Passive | Flat |
| 2 | Guided | Fitting |
| 3 | Inviting | Earned |
| 4 | Compelling | Resonant |

Since v8, Anticipation asks how the stated contract (types, operation names and
compact laws) prepares the reader for what the code must realize. Suspense,
puzzles and withheld reveals score below a plain statement of the same
relationship. Payoff asks how visibly the definitions realize that contract: a
law checked by its proof resolves most, then a law that holds by construction,
and prose answers or reveals resolve nothing. Confirmation and surprise can both
qualify. Tiny
helpers need only provide an immediate, guided setup and fitting resolution;
extra buildup earns no credit. Keep both distributions separate from overall Delight: neither their
average nor one exceptional score can substitute for the other requirement.

Big brain level 4 rewards an unusually economical solution. Level 5, **Galaxy
brain**, rewards a surprising reframing: apparently essential distinctions become
consequences of one principle, revealing further connections that can be traced
through the supplied mechanism. Complexity or obscurity alone does not qualify.
The new level is a user-requested taste criterion; human calibration remains
pending. Earlier receipts retain their original rubric identity and cannot be
reused as ratings under the expanded scale.

### Expressive role and helper requirements

| Scope | Compression | Delight | Memetic identity | Anticipation | Payoff |
| --- | --- | --- | --- | --- | --- |
| Supporting declaration | 3 | 3 | 2 Recognizable | 2 Guided | 2 Fitting |
| Leading or uncertain declaration | 3 | 3 | 3 Contagious | 3 Inviting | 3 Earned |
| Complete explicit mechanism | Galaxy 5 only when relevant | Declaration checks | 3 Contagious | 3 Inviting | 3 Earned |

Each applicable target still requires at least **60% probability mass** at or
above its level. Compression and Delight are relative to the helper's actual
obligation: one exact access/default operation can qualify without invented
abstraction or a separate revelation. The three scaled axes reward a helper's
contribution to the surrounding vocabulary, convention and reading path.
Names, argument permutations, detours and decorative relays earn no automatic
credit merely because they repeat a motif. Judge their actual expressive pull
on memetic identity, and their economy and readability on the other axes.

Supporting means a bounded subordinate operation, such as access/default,
boundary handling, conversion, construction or a thin adapter. Leading means
the organizing representation, central recurrence, domain relationship or
substantial composition. Public visibility, recursion and safety importance do
not determine the role. A function named `helper` may carry the central algorithm.

At least 60% leading probability selects `leading`; at most 40% selects
`supporting` only with adequate context. Missing or truncated context, unknown
collaborators, or an intermediate distribution produce `uncertain`, preserving
the stronger targets. Known Base references alone do not make context uncertain.
Malformed or missing answers fail review. Inspect classifications against actual
responsibility rather than changing names to obtain the lower bar.

The complete mechanism receives its own leading-level identity, Anticipation and
Payoff judgment. It is required even when task potential is low or unavailable,
and even when every declaration is classified supporting. This prevents a
collection of ordinary helpers from substituting for the main expressive idea.

### Potential profundity and composition

Supply a fixed task/contract with `--task=path/to/SPEC.md`, or an explicit
`--cohort` description. The task file takes precedence for the potential judgment.
The generic default scope is not evidence of low potential. The provider rates
only the task text and the potential rubric first: no implementation, source
path, current score, earlier failure, or inducer is in this request.

| Potential level | Meaning |
| --- | --- |
| 0 | Routine obligation; clear direct execution captures its content |
| 1 | Local structure; fitting representation absorbs local cases |
| 2 | Generative structure within the task, without an established deep reframing opportunity |
| 3 | Substantial opportunity for a surprising principle and non-obvious connections |
| 4 | A foundational opportunity joining distinct models or domains |

This is a relevance axis, not a score to maximize. Importance, task size,
implementation difficulty and a domain's reputation for depth are insufficient.
Judge the original obligations; adding machinery or inflating the task does not
justify a higher target. A small problem can still offer deep structure.

Probability mass at levels 3–4 of at least 60% makes Galaxy brain relevant.
Mass of at least 60% at levels 0–2 keeps the role-scaled declaration and ordinary
composition targets.
Between those bounds, or without adequate task evidence, relevance remains
unresolved and Galaxy brain is advisory. It does not prevent an ordinary style
pass or become a claim that Galaxy brain was achieved. This intentionally
permissive default follows the user's preference to under-constrain the ambition.

When relevant, **Galaxy-brain level 5** is added to the three composition
requirements. The composition judgment uses complete selected files and the
collaborator representation specified by its context policy within a 48 KB
source bound. It is not an average or maximum of helper ratings. Missing
imports, unknown required context, parse failures or the size cap leave the
composition requirement unavailable. Source hashes and actual scope remain in
the receipt; this is not a claim to have reviewed an unseen whole project.

The composition judge receives the fixed task, when available, and source group
without previous scores or the potential verdict. Each memetic, Anticipation and
Payoff question sends the composition instructions with that axis's level labels,
not its declaration instructions. This is the deliberate v5 request form under
which the v5 controls ran. Sending each axis's own instructions is an
uncalibrated candidate for a paired comparison, not the production contract.
Each required distribution
must independently reach 60%. Helpers retain their ordinary conceptual-compression bar; a good helper
need not independently be profound. Source ratings, task relevance and composition
quality remain distinct in reporting and receipt reuse.

Version 3 tied Galaxy brain to declaration criticality and made Anticipation and
Payoff mandatory for critical or uncertain declarations. Version 4 changed only
Galaxy relevance and scope. Their original ratings remain historical evidence;
version 5 does not reinterpret them or alter deterministic correctness gates.

Criticality includes a defining or supporting material role in a contract, core
algorithm, invariant, trust boundary, valid state representation or proof
obligation. Even marginal contract importance qualifies. Noncritical requires
an incidental, cosmetic or illustrative role with no material contract role.
Size and current elegance do not determine importance; poorly written critical
code is still critical.

Criticality of at least 60% is `critical`; at most 40% is `noncritical` only when
context is not truncated. Intermediate or context-limited judgments are
`uncertain`. In version 5 this is context, independent of expressive role and
style qualification. A missing or malformed answer still fails review.

For declaration big brain, sum normalized mass at levels 3–5. The additional
composition requirement, when relevant, uses **level 5 alone**. Delight and memetic
identity, Anticipation and Payoff use levels 2–4 for supporting declarations and
3–4 for leading, uncertain and whole-mechanism judgments. Each distribution is
judged separately:

- At least 60%: `meets_target`.
- At most 40%: `below_target`.
- Between those bounds: `uncertain`.

All five applicable targets must be met for a declaration to pass automatically.
Truncated context makes Anticipation and Payoff `unavailable`, without fabricating
a zero score. An unavailable required rating prevents a pass. Unresolved
references are disclosed as `limited_context`; inspect whether the missing
material is necessary to judge the supplied expression.

Receipts retain `rubric_version`, `criticality.policy`, `style_role.policy`, all
returned distributions in `rows[].answers`, and both classifiers' assessments.
Each required style assessment
records its effective `target_level`, `minimum_probability` and `target_basis`.
`diagnostics.assessments` records both reading-experience scales, their context
limits and whether each is required or advisory. `style_summary.by_axis` counts
only applicable requirements. Rankings remain a secondary view of the three
primary axes. Reuse validates every requested answer; policy and wording changes
invalidate old receipts through the rubric hash. Receipts also retain
`potential_profundity`, `composition` and the run-level `qualification`. A
declaration-only `style_summary.meets_all` cannot establish run qualification.

The 60% policy is an explicit provisional review threshold, not a calibrated
probability of agreement with the user. Full distributions remain available;
model confidence is distribution concentration, not correctness or taste agreement.
A model can misclassify importance or expressive role; review both alongside the
source and its contract. Calibration of the classifiers remains separate from proving
that the command enforces its selected threshold.
A high rank alone cannot satisfy the quality bar. Even the first-ranked item can
be below target.

Exit 0 means complete, current coverage, all selected units meeting their bars,
and all mandatory composition requirements met. Advisory or unassessed Galaxy
brain is reported separately and does not prevent an ordinary style pass.
Exit 3 means style attention is needed: a below-target, uncertain or unavailable
required rating, or stale source.
Exit 1 means the run failed or coverage is incomplete. These checks guide review;
they do not replace semantic gates or authorize changing a correct contract.

Inspect low-rated code, identify a concrete improvement, and retain the original
contract and independent tests. Record disagreements and compare actual proposed
changes when available. Do not force obscurity, branding, verbosity or churn to
satisfy the model. Human preferences and held-out examples must guide calibration.

Perch 0.3.5's ordinary custom-check path expects Noul answers. This project's
companion command supplies the Score path through the same provider and existing
project credentials. Normal `npm run lint` still reports defect/performance/law
checks; **it does not include these style ratings**. During development, run both
applicable checks and report their coverage separately.

The complete project pass and a live example are recorded in
[the three-axis report](perch-style-project-2026-09-26.md).
That report predates version 3. Historical version-3 focused verification and
live context-limit checks are recorded in
[the version-3 integration evidence](perch-calibration/style-v3-2026-09-27/README.md).
Version 5's [bounded controls and observed misses](perch-calibration/style-v5-2026-09-27/README.md)
support the helper scope change but do not establish broad model accuracy.

The user has started an [implementation campaign](STYLE-CAMPAIGN.md) to improve
the whole inventory. Its owner queue, continuation policy and receipt-aware
baseline inventory live in `docs/style-campaign/`. The campaign preserves
independent acceptance and records unresolved taste judgments explicitly.
Its inventory's `matches_all_required_baseline_targets` field includes the
conditional requirements for historical v3 receipts. Under v4 this per-unit
inventory exposes declaration-baseline matches separately and conservatively
requires a current task/composition review; individual rows cannot establish
run-level qualification. The legacy `matches_all_three_baseline_targets` field
remains a conservative alias. Older rubric identities are incompatible
with the current baseline comparison.

## Historical two-axis comparison pilot

The pilot below used version 1, required competing implementations, and did not
include the memetic axis. Its distributions are historical evidence and must not
be combined with the current rubric as if the instructions were identical.

### Pilot — 2026-09-26

Three [specimens](../tests/perch-style/README.md) implement the same list mapping.
The frozen performance evaluator independently accepted all three: Bend 2.0.29
compilation, 19 output probes per candidate, and operation-count scaling through
1,024 elements. These finite gates do not prove arbitrary-input equivalence or
safe stack depth on every backend. Five targeted `perf-growing-prefix-copy`
checks covered every declaration, with zero findings.

Two live runs used `jev-1.13.0`, with the second reversing request order.
Both returned the same rank order, with small changes in scores and distributions:

| Implementation | Maximally big brain | High dopamine to read |
| --- | ---: | ---: |
| Direct recursion (`a`) | 3 | 3 |
| Mapping combinator (`b`) | 2 | 1 |
| Accumulator and reversal (`c`) | 1 | 2 |

**Every adjacent pair was a near tie on both axes.** In the first run, big-brain
means spanned only 2.31–2.39; delight means spanned 2.43–2.71. This confirms a working ranking
path with two distinct orderings, not strong aesthetic separation. Repeating
identical requests may benefit from provider determinism or caching; these two
runs are not independent evidence of judgment quality. The rubric was not tuned
to make a particular specimen win.

The two runs made six requests with 12 Score answers, consuming 7,376 input
tokens and 234 output tokens. They took 521 ms and 316 ms respectively. Timings
measure these runs only and do not establish sustained provider latency.

Evidence: [first ranking](perch-calibration/style-2026-09-26.json),
[reverse-order repeat](perch-calibration/style-reversed-2026-09-26.json),
[deterministic gates and source-rule receipts](perch-calibration/style-gates-2026-09-26.json).
Twenty-one offline tests and the law-rule wiring gate passed, including malformed
answers, missing credentials, partial failure, model drift, exact declaration
selection and secret-free receipt checks.

That pilot's proposed next step was a comparison of real compiler alternatives.
The user's later instruction supersedes comparison-only coverage: routinely
assess existing declarations against the three quality targets. Human preferences
recorded before review and fresh held-out examples are still needed to calibrate
agreement with the intended taste. Track unwanted obscurity, verbosity and novelty
incentives separately from defect precision; preserve deterministic acceptance.

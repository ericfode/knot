# Modules review round 4

Round 4 had six confirmed findings. Five are fixed. The sixth, a documentation
finding, is fixed in the documents; the coordinator acknowledgement it asks
for is still open. Each code finding had its seed observations, or for the
output guard its literal review, frozen in
[`review-round4.json`](review-round4.json) before its repair. Every earlier
fixture, expectation and pinned host observation is unchanged.

| Finding | Freeze | Repair | Disposition and evidence |
| --- | --- | --- | --- |
| A climbing `--bundle` spelling escapes bundle containment (blocking) | `c19600f` | `cbf35bc` | **Fixed.** `--bundle ../w/lib` and the import `../../w/lib/extra/flag.bend` report `Unsupported load path-identity`. They were Checked; the seed rejects both. The plain `--bundle lib` control stays `Invalid load import-path`. `--bundle .` was also Checked; it now contains every relative path and reports `Invalid load import-path`, as the seed does. |
| Module identity is lexical, so one file loads twice (blocking) | `c19600f` | `cbf35bc` | **Fixed.** Two spellings under two aliases were Invalid type-mismatch; the seed prints Lit. A single climbing import was Checked with namespace `../../w/app/m/flag`. A climbing back edge was Invalid cycle. A climbing entry was Checked. All four now report `Unsupported load path-identity`. A non-climbing relative control still runs to Lit and is audited with relative module paths. |
| A string continuation line starting with `import` is Invalid (blocking) | `d4e3e6a` | `1ab6394` | **Fixed.** In three seed-accepted programs, a multi-line literal closes on a line that begins with an `import`: a module import, `import Base` and a quoted foreign import. The module lanes now report `Unsupported lex literal`, as the single-file lanes do. |
| Documents claim unchanged single-file behavior (major) | — | this round's documentation commit | **Fixed in the documents; the acknowledgement is open.** `src/CONTRACT.json` `legacy_commands`, `src/SPEC.md` and both READMEs now list the single-file deltas. |
| Seed-accepted result types are Invalid (major) | `2f3d5af` | `a50bbb5` | **Fixed** in the module lanes and, where Base is not needed, the single-file lanes. The result types are `-> IO(Unit)`, `-> Light & Light`, `-> (Light)`, `-> Light -> Light` and an equality type. They report `Unsupported parse result-type`. A missing colon and a missing type stay `Invalid parse function-result`. |
| `compile --bundle` can overwrite a module or Base (major) | `c49ff88` | `532aef0` | **Fixed.** Eleven literal cases pass in both lanes. Nine are refused: an imported module named absolutely, relatively and with dots; `./main.bend`; both mixed-basis spellings; a symlinked output; a climbing output; and a private real-file Base copy named relatively and absolutely. In each refused case the named file keeps its bytes. A fresh output is still Built. |

The coordinator still needs to acknowledge the single-file changes from finding 4. They were justified only in commit messages and in
[REVIEW-ROUND-3.md](REVIEW-ROUND-3.md):

- round 3 extended the let-binder rule to arm and field binders;
- round 3 removed the field-binder test from `patterns.bend` and its two helpers from `catalog.bend`, which is fields-increment code;
- round 4 adds the result-type and spaced-arrow changes to the single-file lanes.

## Mechanism

**Climbing paths.** The path query returns one bit and cannot name the working
directory. A relative spelling that still begins with `..` after normalization
therefore has no canonical form. `imports.climbs` names that condition.
`load.start` applies it to the entry and the bundle root. `imports.resolve`
applies it to every target before any containment, namespace or package-escape
decision. The normalized working directory is `""`, and
`imports.bundle_prefix("")` is now `""`, so it contains every relative path.

**Quoted bodies.** A string literal is the only seed construct that spans lines.
`imports.header_lines` records whether any body line has held a double quote.
After that, an `import` line is no longer judged by its first word. It stays
body text: the lexer reports a real literal, and the parser reports a
misplaced import.

**Result types.** The parser reads a result as one bare name followed by `:`.
It still reports `type-application` at `<`. Any other continuation, or a
result head that is not a name, is `Unsupported parse result-type`, which
mirrors `parameter_end`. A missing name or colon (`:`, a newline or end of
input where the type or colon belongs) stays `Invalid parse function-result`.

The seed reads `->` as one word, but the lexer produces `-` and then `>`. A
function is now built only when the two tokens are adjacent. Knot had accepted
the spaced `- >`, which the seed rejects. That over-acceptance predates this
increment; it was found while repairing this function and is fixed with it.

**Output guard.** `driver.bundle_to` runs `load.guarded` between loading and
checking. The output first passes the same path query as the sources. It must
not climb (`HostFailure arguments output-path`). It is then compared with the
entry, every loaded module and the Base path (`HostFailure arguments
source-is-output`). Canonical spellings on one basis must be equal to match.
Across bases, a match is an absolute spelling that ends with the relative
one. The compiler CLIs' foreign-dependency lists are unchanged.

## Laws, fixtures and mutants

Seven new filled laws. The five module laws make 94 in the modules gate's four
proof entries: loader and path 33, qualification 26, Base selection 20, pin
helpers 15. The two frontend laws bring `src/PROOF.bend` to 18. Each law was
checked in a scratch copy: it prints `All terms check.` unmutated and fails at
its own location under its matching mutation. The two output laws fail under
two mutations each.

- `climbing_paths_have_no_identity`
- `working_directory_bundle_contains_local_paths`
- `quoted_body_leaves_imports_to_the_lexer`
- `output_names_no_file_the_load_read`
- `uncanonical_output_is_refused`
- `longer_result_type`
- `spaced_result_arrow`

These are helper/transition laws, not a theorem of compiler correctness.

Round 4 freezes 22 seed fixtures, one seed call each, and 11 literal
output-guard cases. The seed fixtures are four containment, five identity,
five string and eight result-type cases. Ten of them also run the
single-file CLIs in both lanes.

The containment and identity cases run from a directory inside the copied
round folder. Their entry and bundle spellings are literal and relative, the
same for the seed and for Knot. Every climb stays inside the copy, so the
cases do not depend on the scratch root.

The gate has eleven new type-correct semantic mutants, each killed by its
frozen witness:

- `climbing-target-accepted`
- `climbing-root-accepted`
- `working-directory-bundle-empty`
- `quoted-import-classified`
- `result-type-invalid`
- `spaced-arrow-accepted`
- `output-guard-files-ignored`
- `output-guard-base-ignored`
- `output-guard-single-basis`
- `output-query-ignored`
- `output-climb-ignored`

The five output mutants are built from the mutated compiler CLI and run their
literal case in a private copy.

## Preflight

All preflight runs were offline and made no provider requests.

- **Manifest.** 23 groups, 1,400 declaration occurrences, all 23 compositions
  available. No truncated or role-limited declarations and no structural
  blockers. `frontend-parsing` is 21,284 bytes, `module-loading` 32,872 and
  `checking` 47,400, all under the 48,000-byte bound.
- **Direct.** The nine changed implementation, law and proof files hold 259
  declarations, with 46 truncated or role-limited contexts: 6 caller/byte,
  9 file and 32 helper limits. The combined composition is oversized: 173,688
  bytes against the 48,000-byte bound. That gives 47 structural blockers.

No style rating or style pass is claimed. Live Perch review remains with the
coordinator.

## Known limits

- **Climbing relative spellings are Unsupported even when the seed accepts
  them**, for example `entry-climbing`. Canonical identity for them needs a
  host query that can name the working directory; `path_identity` returns only
  a bit.
- **The quote rule is coarse.** If a quote appears in a comment or a character
  literal, a later misplaced import goes to the parser. It then reports
  `Unsupported parse import` instead of `Invalid load import-after-declaration`
  (frozen `comment-quote-import`).
- **The output guard compares canonical spellings.**
  - It cannot see hard links.
  - Base can still be overwritten when the toolchain symlink's target
    directories are not named `.toolchain/bend-2.0.29-574b6d3/bend2`, and the
    output is an absolute path to that real file.
  - A distinct absolute output whose tail equals a loaded relative spelling is
    refused.
  - Outputs under a symlinked directory, such as macOS `/tmp`, are refused;
    name the real path instead.
  - The single-file compile lane keeps its string-only check, so `main.bend`
    against `./main.bend` is still not caught there.
- **Pre-existing D4 gap, outside this round:** `def main?() -> T` (the unsafe
  marker) is `Invalid parse expected-(`, although the seed accepts it.
- **The selfhost suite's `modules` and `packages` needs stay unflipped.**
  Merging them is the coordinator's decision.

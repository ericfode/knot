# Poly fixture suite (campaign increment `poly-fixtures`)

This suite freezes the expectations for the `poly-fixtures` increment of the
[VM-first design](../../docs/compiler-campaign/VM-DESIGN.md). It covers the
checker residue that Knot's own source needs and that no other frozen suite
covers: closures and function values at generic and erased-type arrows,
higher-rank `IO(A)`-shaped arrows, quantity-polymorphic `Kind(a)` parameters,
template binders (`~A`), and Sigma pairs declared outside Base. Two later
increments consume it:
- `poly-closures` must make the `generic-arrows`, `higher-rank` and
  `kind-polymorphism` fixtures agree;
- `templates` must make the `templates` and `sigma` fixtures agree.

The suite was written before any implementation (D4, D7) and independently of
the implementers. Seed-valid programs take their results from the pinned
reference interpreter, Bend 2.0.29 at `574b6d3`. Knot-specific outcomes are
reviewed literals in `expectations.json`. No expectation comes from Knot
output, and `regen.py` never runs Knot.

The implementers wire the gate runner and do not edit these expectations.
Changing a fixture, a case or a pinned outcome is a separately reviewed amendment.

## Scope

The scope comes from the census in
[`implementation.json`](../../docs/compiler-campaign/inventory/implementation.json)
under `generics`, `higher-order`, `templates` and `dependent`, plus the
`quantities.arguments`, `quantities.polymorphic`, `function-values` and
`calls.partial` classes. It is restricted to Knot's own source:
- every non-law file in `src/`. This includes the bundle S that VM-DESIGN.md
  defines as `src/compile-cli.bend` and its imports, and also `check-cli`,
  `parse-cli`, `eval-cli`, `eval` and `checked-display`, which S does not
  import but `vm-e2e2` and the conformance runs compile;
- the reached slice of the pinned Base;
- the bytes package that S imports
  (`0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend`, published from
  `packages/output_builder/bytes.bend`).

The census also scans package modules that no `src/` file imports: `int_map`,
`source`, `symbols`, `term_store`, `vec` and `output_builder`'s `main.bend`.
Their shapes in these classes are listed at the end of the appendix but are
not required.

Each seed-valid fixture mirrors named shapes in miniature, in the compact spelling Knot uses:
no space after a comma in a call, and `case K{..}: e` on one line. Each case's
`mirrors` field cites `path:line name`. Line numbers are those at this suite's
base commit; `base.bend` is the pinned `.toolchain/bend-2.0.29-574b6d3/bend2/base.bend`.
[Census coverage](#census-coverage) maps every census declaration in these
classes to the fixture that covers it.

**Shapes in Knot source.** These are the shapes that `src/` writes, or that
its calls land in within the reached Base slice
([`base-closure.json`](../../docs/compiler-campaign/inventory/base-closure.json)
reaches `IO`, `IO.bind`, `IO.die`, `Pair`, `Sigma`, `Result`, `List.length`,
`List.append`, `List.reverse` and `List.reverse.go`).

| Shape | Where | Fixtures |
| --- | --- | --- |
| `S.choose(-A: Type, c, yes: Unit -> A, no: Unit -> A)` (with `S.bind`, about 300 call sites by VM-DESIGN.md's count), instantiated at `Result<S.Error,State>`, `List<&2,Token>` and `Maybe<&2,C.Term>` | `src/syntax.bend:76`, `src/syntax.bend:98` (skip_lines), `src/lex.bend:12` (normal, four chained), `src/lex.bend:35` (step_at), `src/parse.bend:54` (wrap_call) | `choose-rigid`, `choose-result-chain` |
| `S.bind(-A: Data, -B: Data, r: Result<Error,A>, next: A -> Result<Error,B>)` at `List<&2,S.Token>`, `P.Parsed` and `List<&2,U32>`, nested, the inner lambda capturing the outer binder | `src/syntax.bend:81`, `src/driver.bend:30` (source), `src/driver.bend:69` (ordinals), `src/lex.bend:67` (scan) | `bind-instance-chain`, `bind-rigid-caller` |
| `+` lambda binders at generic instances: `+params =>` at `List<&2,C.Parameter>` as `S.bind`'s continuation binder, `bound => +fields =>` on a second curried binder, `+token => mark =>` | `src/check.bend:182` and `:211` (run), `src/patterns.bend:38` (fields), `src/patterns.bend:68` (branch), `src/wasm.bend:274` (profiled) | `bind-promoted-instance` |
| lambdas created inside generic code at rigid arrows: `x => f(x,R,k)` captures `f: A -> IO(B)` | `base.bend:155` (IO.bind) | `choose-rigid`, `bind-rigid-caller`, `generic-compose`, `generic-capture` |
| curried continuations into `Result` instances, one captured in a choose thunk whose body is a let then a call | `src/patterns.bend:14` (add), `src/check.bend:165` (arm_scope), `src/parse.bend:43` (then), `src/check.bend:141` (call_body), `src/core.bend:39` (exhausted) | `curried-generic-continuation` |
| `IO(A) = @-R: Type -> @k: (A -> IO.OP<R>) -> IO.OP<R>` with `bind` and `die` | `base.bend:147`, `:155`, `:184` | `rank2-pure-bind`, `rank2-two-answers`, `rank2-param` |
| `next: C.Book -> IO(Unit)` threaded through `checked`, `read_result`, `opened` and `load`, and captured by a bind lambda | `src/driver.bend:15`, `:39`, `:50`, `:55` | `rank2-continuation`, `rank2-try` |
| `IO.bind(..,opened(characters,depth))` (partial application) and `IO.bind(..,IO.args(),arguments)` (a named def) | `src/check-cli.bend:39`, `src/check-cli.bend:45`, `src/parse-cli.bend:56` | `rank2-partial-bind` |
| `S.choose(IO(Unit),..)`: `choose`'s erased `-A` at a rank-2 action type (impredicative instantiation), one thunk dying and the other loading with a continuation that captures `+` parameters | `src/check-cli.bend:51` (configure), `src/parse-cli.bend:43` (configure), `src/compile-cli.bend:44` (configured) | `rank2-choose-action` |
| statement-only `do IO<Unit>:`: a statement, then the tail action, with no `<-` and no `return` | `src/driver.bend:46` (read_pair), `src/check-cli.bend:35`, `src/parse-cli.bend:27`, `src/compile-cli.bend:17` (write_pair) | `rank2-do-block` (boundary) |
| `List.length(&2,S.Node,args)`, `List.reverse(&2,S.Token,..)` into Base's `a, -A: Kind(a)` definitions; `List.reverse` forwards `a, A` to `List.reverse.go` | `src/check.bend:55`, `src/lex.bend:55` (finish), `src/eval.bend:133`, `base.bend:814`, `base.bend:835`, `base.bend:843` | `kind-closure-list`, `kind-forward` |
| the two-quantity family `Result<a, b, -E: Kind(a), -A: Kind(b)> is Kind(a <&> b)`, spelled long as `Result<&1,&1,..>`, and its short form `Result<S.Error,A>` | `src/syntax.bend:81`, `base.bend:36` | `kind-two-quantities` |
| a Sigma inside a `Result` inside an action: `IO.bind(File & Result<&1,&1,U32 & String,String>,Unit,File.read(..),read_pair(..))`, then `(file,result) = pair` and `case Fail{(code,message)}` | `src/driver.bend:50` (opened), `src/driver.bend:44` (read_pair), `src/check-cli.bend:28` (read_result), `src/check-cli.bend:39` (opened) | `sigma-in-result-action` |
| `List<&1,Result<S.Error,String>>` folded through `S.bind` with a `Con{Done{+head},tail}` pattern | `src/diagnostic.bend:25`, `src/wasm-bytes.bend:18` | `kind-result-list` |
| `set_known(~A: Data, ~value: A -> S.Token -> U32 -> C.Term, ..)`, with `refine` and `replace` passing closed lambdas whose binders shadow their own parameters | `src/scope.bend:77`, `src/scope.bend:85`, `src/scope.bend:108` | `template-set-known-thunk` |
| `Pair(A,B) = Sigma<&1,&1,A,_ => B>`, spelled `File & Result<..>` and destructured by `(file,result) = pair`; `Sigma`'s field `snd: B(fst)` | `base.bend:127`, `base.bend:25`, `src/driver.bend:44`, `src/check-cli.bend:33` | `sigma-pair`, `sigma-dependent` |
| `unpack(-A,-B,-R, pair: A & B, f: A -> B -> R)`, a census `dependent` and `higher-order` declaration of `vec`, a package the census scans but no `src/` file imports; its `(a,b) = pair` is the destructuring Knot's `read_pair` writes, here under rigid types | `packages/vec/main.bend:97` (the census records it at line 101 of the published package `0xd684886d…`) | `sigma-unpack` |

**Base shapes outside the reached slice, and edges.** These fixtures are not
reached by Knot's source today. Each exercises the same machinery in a form
Knot's source would reach the moment it calls one more Base def, or pins an
adversarial case that the owning increment must not reject:
- `IO.pure`, `IO.pass` and `IO.try` (`base.bend:152`, `:187`, `:194`) are not
  in the reached slice. `src/driver.bend:39` (read_result) and `:50` (opened)
  write their bodies by hand: a match on a `Result`, then `IO.die` or the
  continuation. They ground `rank2-pure-bind` and `rank2-try`. `rank2-try`
  passes `Act.pass(A)` exactly as `IO.try` passes `IO.pass(A)`: a generic def
  applied to its erased type argument alone, used as a function value.
- Base's templates are not reached: `List.map(~A: Type, ~B: Type, ~f, ..)`,
  `List.filter(~A: Data, ..)`, `List.foldl(~a: Quant, ~A: Kind(a), ~B: Type, ..)`
  and `List.any` (`base.bend:807`, `:952`, `:959`, `:977`). scope.bend's
  `~A: Data` is the only template binder Knot writes. These fixtures pin its
  generalizations: type binders (`template-map-types`), a `~A: Data` forwarded
  as an erased argument (`template-filter-data`), and quantity and kind binders
  (`template-fold-quant`, `template-any-forward`). D2's whole-Base milestone
  needs all of them, and the VM design lists `List.map` for baseslice-check.
- `Maybe.map` and `Maybe.bind` (`base.bend:739`, `:713`) are not reached. Knot
  passes `Maybe<&2,U32>` beside a continuation instead
  (`src/catalog.bend:50`, constructor_next). `kind-higher-order` pins arrows
  whose types range over `Kind(a)`.
- `Exists` and `Map.to_list` (`base.bend:130`, `:2828`) are not reached. They
  are Base's uses of a family that computes a type, and of a `&2` Sigma inside
  a list. `sigma-dependent` and `sigma-reusable` pin those two uses of the
  reached `Sigma`.
- Edges with no counterpart in any source:
  - `generic-arrow-instances`: a type argument that is a rank-1 arrow. The only
    arrow-valued type argument in `src/` is `IO(Unit)` at
    `src/check-cli.bend:51`, which is rank-2 and pinned by
    `rank2-choose-action`. The fixture cites that line as its nearest shape.
  - `rank2-two-answers`: one action type at two answers.
  - `rank2-param`: rank-2 parameter types written out.
  - `kind-zero-arrow`: `Kind(&0)` at an arrow.
  - `template-generic-arg`: closed `~` arguments built from generic defs.
- `rank2-two-answers` also instantiates `Act` at `Act(Flag)` (`Act.join`).
  That is impredicative instantiation: an erased `-A: Type` takes a rank-2
  type. Knot's source needs the same mechanism, because
  `S.choose(IO(Unit),..)` instantiates `choose`'s `-A` at `IO(Unit)`
  (`src/check-cli.bend:51`, `src/parse-cli.bend:43`,
  `src/compile-cli.bend:44`). So `poly-closures` owns it, and the fixture is
  `agree`, not a boundary.

Out of scope:
- **Shapes already frozen elsewhere.** These are covered by other suites and
  not repeated here: monomorphic closures (closures suite), `S.choose` and
  `S.bind` with plain enum instances (`dependent-choose`, `dependent-bind`,
  `generic-choose-bind`), the two-parameter `set_all` template, a partial call
  and a function value at `then(-A,-B,x,next)`, `core.invalid` (sugar suite),
  and `Kind(a)` walks over data and boxes (generics suite).
- **Laws.** The census lists 120 `dependent` declarations in `src/`. Of these,
  110 are law and proof declarations in `*-LAWS.bend` and `*-PROOF.bend`. Their
  types mention earlier `for` binders inside equality types, and none is
  reachable from a CLI entry. The other ten are covered here and in the sugar
  suite.
- **IO effects.** No fixture imports Base. `Act(A)` reproduces `IO(A)` with
  fixture types (`Op<R>` for `IO.OP<R>`, `Halt{code: Fault}` for
  `Halt{code,message}`). Foreign effects belong to the io suite and `io-check`.

## Contents

- `fixtures/*.bend`: 61 small programs, one shape or edge each.
  - Every fixture is ASCII with LF line endings and no tabs. Line 1 is a
    `# summary`, which `regen.py` checks against the case's `summary`.
  - No fixture imports anything, not even Base. Each declares its own enums
    (`Flag`, `Color`, `Fault`, and so on) and its own carriers. The carriers copy
    Base's declarations: `Res<a, b, -E: Kind(a), -A: Kind(b)> is Kind(a <&> b)`,
    `Seq<a, -A: Kind(a)> is Kind(a)`, `Opt<a, -A: Kind(a)> is Kind(a)`,
    `Op<-R: Type> is Type` and
    `Dep<a, b, -A: Kind(a), -B: @-x: A -> Kind(b)> is Kind(a <&> b)`.
  - Every fixture declares `main()`. Seed-valid fixtures have a `main` plus a
    few entries. Entries take and return only nullary enums declared in the
    fixture, because the host boundary is enum-only. Every closure, action,
    template instance and pair is built and consumed inside the program.
  - Every negative is its twin plus one reviewed edit. Besides the summary
    line, the edit is at most two diff hunks: a changed line, or an added
    definition built from the twin's own declarations plus the caller line
    that uses it (`rigid-closure-twice`, `kind-quantity-mismatch`,
    `kind-reuse-affine-result`, `sigma-reuse-affine`). The edit is visible with
    `diff fixtures/<twin>.bend fixtures/<negative>.bend`. The seed's error line
    lies in a declaration the edit adds or changes. The error is the intended
    one, and the `seed_reason` substrings pin it.
    Where a second error is unavoidable (`kind-closure-at-data`,
    `template-quant-kind`), only the `Invalid` class is pinned.
- `expectations.json`: all expectations, in these sections:
  - `seed`: version, revision and launcher path. These must equal `src/CONTRACT.json`.
  - `commands`: how every observation was produced.
  - `requirements`: the four Knot requirement kinds, defined below.
  - `increments`: what `poly-closures` and `templates` own.
  - `needs`: the capability vocabulary for `requires`.
  - `cases`: hand-reviewed metadata for each fixture. It records the class,
    feature, owning increment, summary, census classes, mirrored shapes, twin,
    needs and entry signatures. Negatives also record the seed's rejection
    reason. Every case ends with its Knot outcome block. A pinned code also
    names its `precedent`, the frozen fixture that already uses it.
  - `observations`: generated by `regen.py`. It holds the seed file hashes and
    the Bun version. For each fixture it holds the source hash, the enum
    constructor orders, the `--check-only` and run results, and every entry
    call. A call records its wrapper source, argv, exit code, exact stdout and
    stderr, and its result `{type, constructor, tag}`. `tag` is the
    constructor's position in its declaration.
- `regen.py`: re-runs the seed and diffs the output against `observations`.

## Regenerating and checking

```sh
python3 tests/compiler-poly/regen.py          # re-run the seed; exit 1 on any difference
python3 tests/compiler-poly/regen.py --write  # rewrite observations only; review the diff
```

The script runs the seed as `bun .toolchain/bend-2.0.29-574b6d3/bend2/main.ts`,
from the repository root, with `BEND_NO_TELEMETRY=1` and relative paths. Its
recorded output does not depend on the checkout. A check takes about 15
seconds. `--write` runs the seed twice and writes only if both passes agree.
Wrappers are written to the ignored `.local/compiler-poly/wrappers/` directory.

- **Observation shapes.** For `main`, the observation is a direct run of the
  fixture, so stdout is unqualified (`On{}`). Every other entry is called
  through a wrapper that imports the fixture as `F`. Its stdout therefore
  carries the import path, `../../../tests/compiler-poly/fixtures/<case>.On{}`,
  and `result` strips that prefix.
- **Failure conditions.** It fails in any of these cases:
  - the fixture files differ from the cases;
  - a summary line differs, a fixture imports something, or `main()` is missing;
  - a class, requirement, increment, need, census class or mirror citation is
    malformed or inconsistent, a feature is not owned by the case's increment,
    or a census class is not one of `implementation.json`'s;
  - a need that is visible in the syntax (`destructuring-let` for a
    `Ctor{..} = e` let, `do-notation` for a `do` block, `nested-patterns` for
    a nested constructor or wildcard pattern) is required without its form, or
    the form occurs without the need;
  - a negative does not name a seed-valid `agree` twin of the same feature and
    increment, or a seed-valid fixture names one;
  - the reviewed sections (everything but `observations`) differ from the
    `REVIEWED_SHA256` constant in `regen.py`, or `NEEDS` and `INCREMENTS`
    there differ from the `needs` and `increments` sections;
  - a pinned code has no precedent, or a precedent is not a reject case of its
    frozen suite that pins the same code (or leaves it open where this case
    does);
  - a `seed_reason` entry is empty, or none of them anchors the error with a
    `Location:` or an `NN>|` line;
  - a negative differs from its twin by more than two hunks besides the
    summary line, or the seed's error line falls outside the declarations
    that the edit adds or changes;
  - a boundary names no need that puts it outside both increments
    (`do-notation`);
  - the seed accepts a fixture marked `reject`, or rejects one that is not;
  - a negative's `seed_reason` substrings are missing, meaning the seed
    rejected it for a different reason;
  - an entry is not declared with exactly its recorded enum parameters, or uses
    a non-enum type;
  - the calls of a seed-valid fixture yield only one constructor, so a constant
    answer could pass;
  - the seed times out;
  - the seed identity, the seed file hashes or the Bun version changed;
  - a recorded output contains a checkout-specific path.
- **Bootstrapping.** `--write` never touches the reviewed sections. After
  running it, read the diff by hand. A reviewed amendment to a case, a need, an
  increment or any other reviewed section also updates `REVIEWED_SHA256` in
  `regen.py`, in the same change. The failing run prints the new digest.

## Coverage matrix

Classes:
- **positive**: an ordinary program in the owning increment.
- **edge**: an adversarial program the seed accepts.
- **boundary**: a seed-valid program that uses a form outside the owning increment.
- **negative**: a program the seed rejects, next to a named seed-valid twin.

| Feature | Increment | Positive | Edge | Boundary | Negative |
| --- | --- | --- | --- | --- | --- |
| generic-arrows | poly-closures | `choose-rigid`, `choose-result-chain`, `bind-instance-chain`, `bind-rigid-caller`, `bind-promoted-instance`, `generic-compose`, `generic-capture`, `curried-generic-continuation` | `generic-arrow-instances` | - | `rigid-closure-twice`, `rigid-domain-mismatch`, `rigid-capture-twice`, `rigid-reusable-type`, `bind-arrow-instance`, `choose-branch-mismatch`, `promoted-affine-instance` |
| higher-rank | poly-closures | `rank2-pure-bind`, `rank2-continuation`, `rank2-partial-bind`, `rank2-try`, `rank2-choose-action` | `rank2-two-answers`, `rank2-param` | `rank2-do-block` | `rank2-rigid-answer`, `rank2-continuation-twice`, `rank2-run-twice`, `rank2-monomorphic-arg`, `rank2-choose-mismatch` |
| kind-polymorphism | poly-closures | `kind-closure-list`, `kind-higher-order`, `kind-forward`, `kind-two-quantities`, `kind-result-list` | `kind-zero-arrow` | - | `kind-closure-at-data`, `kind-closure-reuse`, `kind-quantity-mismatch`, `kind-reuse-affine-result`, `kind-meet-reuse` |
| templates | templates | `template-map-types`, `template-fold-quant`, `template-any-forward`, `template-set-known-thunk`, `template-filter-data` | `template-generic-arg` | - | `template-open-type`, `template-type-mismatch`, `template-quant-kind`, `template-plain-param`, `template-thunk-affine` |
| sigma | templates | `sigma-pair`, `sigma-dependent`, `sigma-unpack`, `sigma-in-result-action` | `sigma-reusable` | - | `sigma-snd-mismatch`, `sigma-unrefined`, `sigma-family-live-binder`, `sigma-affine-twice`, `sigma-reuse-affine` |

That makes 27 positive, 6 edge, 1 boundary and 27 negative fixtures, 61 in
all, one above the 40 to 60 the increment aimed for. The audit confirmed the
five added fixtures (`rank2-choose-action`, `rank2-choose-mismatch`,
`sigma-in-result-action`, `bind-promoted-instance`,
`promoted-affine-instance`) as Knot-source shapes that nothing else covers, so
none was cut. They produce 336 seed entry calls and 27 seed rejections. The 33
`agree` fixtures account for 331 of the calls: 226 for `poly-closures` and 105
for `templates`.

The negatives cover each rejection the goal names:
- **An affine capture used twice:** `rigid-capture-twice`, `template-thunk-affine`.
- **A closure or action used twice:** `rigid-closure-twice`,
  `rank2-continuation-twice`, `rank2-run-twice`, `kind-closure-reuse`,
  `sigma-affine-twice`.
- **A rank mismatch:** `rank2-monomorphic-arg` gives a rank-1 function where a
  rank-2 one is expected. `rank2-rigid-answer` answers at `A` where the rigid
  `R` is due.
- **A wrong quantity instantiation:** `kind-quantity-mismatch`,
  `kind-closure-at-data`, `template-quant-kind`, `bind-arrow-instance`,
  `kind-reuse-affine-result`, `kind-meet-reuse`, `rigid-reusable-type`,
  `promoted-affine-instance` (a `+` lambda binder at `Seq<&1,Flag>`),
  `sigma-reuse-affine`, `sigma-family-live-binder`.
- **Template misuse:** `template-open-type`, `template-plain-param`,
  `template-type-mismatch`, `template-quant-kind`.
- **Type errors:** `rigid-domain-mismatch`, `choose-branch-mismatch`,
  `rank2-choose-mismatch` (an action instance at the wrong answer type),
  `sigma-snd-mismatch`, and `sigma-unrefined` (a dependent type that has not
  been refined).

## Knot requirements

| Requirement | Meaning |
| --- | --- |
| `agree` | Knot checks the fixture (exit 0). For every call in `observations`, the evaluator returns the recorded `result.constructor`. Every image or VM lane that exists returns the recorded `result.tag`, under the four-lane rule of VM-DESIGN.md. |
| `agree-or-unsupported` | Either `agree`, or exit 3 with an `Unsupported` diagnostic and no artifact. `Invalid` never qualifies, because the seed accepts. |
| `reject` | Exit 2 (`Invalid`), never `Checked` or `Built`, and no artifact. If `diagnostic` is pinned, stderr starts with it. Otherwise the phase and code are the implementer's to choose, and are recorded when chosen. |

A pinned outcome carries `knot_expected: true` and a one-line justification.
The classification invariant holds for every fixture. When the seed accepts,
Knot never reports `Invalid` (D4). When the seed rejects, Knot reports `Invalid`.

- **Native Wasm profiles.** Native lowering is the speed track (D14). A native
  profile may report `Unsupported` at compile for any fixture here, but never
  `Invalid` for a seed-valid one. The `agree` lanes are check, eval and, once
  they exist, image and VM.
- **Reused codes.** A pinned code reuses the existing vocabulary only where
  the seed gives the same reason as a frozen fixture that already pins it. That
  fixture is the case's `precedent`:
  - `affine-reuse` (closures `closure-call-twice`, `capture-affine-twice`,
    `capture-then-use`; sugar `tuple-affine-reuse`): a closure, a continuation
    or an action applied twice, a capture of one affine value shared by two
    closures, and a field destructured from a `&1` pair used twice.
  - `type-mismatch` (generics `rigid-mismatch`, `wrong-type-arg` and
    `quantity-invariant`; closures `closure-domain-mismatch`): distinct rigid
    variables (`B` and `A`, or `R` and `A`), an instance of the wrong shape
    (including `Act(Flag)` where `Act(Color)` is due), `Seq<&2,Flag>` against
    `Seq<&1,Flag>`, and a function value of the wrong arrow type, including the
    wrong rank.
  - `reusable-type` (generics `reusable-type-param` and `meet-not-reusable`;
    sugar `annotation-reusable-quantity`; closures `reusable-closure-binder`):
    a `+` binder at a `Type` variable, at a `&1` instance (a parameter, a let
    or a lambda binder), or at the meet `&2 <&> &1`.
- **Class-only pins.** These negatives pin exit 2 only:
  - `bind-arrow-instance`, `kind-closure-at-data` and `template-quant-kind`.
    Each gives an arrow type where a `Data` kind is wanted. This is the reason
    generics `kind-type-for-data` leaves open.
  - `template-open-type`. A caller's erased type variable is an open `~`
    argument. This is the reason sugar `template-open-argument` leaves open.
  - `template-plain-param`. The seed refuses `~` at parse when the callee is
    not a template. This is the reason sugar `template-forward` leaves open.
  - `sigma-unrefined` (a stuck `Shade(f)`) and `sigma-family-live-binder` (a
    live binder where the family wants an erased one). No frozen fixture names
    either reason.
- **Open boundary.** `rank2-do-block` is a statement-only `do Act<Color>:`,
  the only `do` form in `src/` (`driver.bend:46`, `check-cli.bend:35`,
  `parse-cli.bend:27`, `compile-cli.bend:17`). `do` desugaring is not a
  `poly-closures` capability, so that increment may report it `Unsupported`,
  but never `Invalid`. The fixture stays `agree-or-unsupported`. The IO
  instance that Knot writes is pinned `agree` by the io suite (`mini-driver`,
  `bind-deep`, `die-codes`; owner `io-check`, with `vm-e2e3`). The `<-` and
  `return` form, which `src/` never writes, is io's
  `Unsupported\tparse\tdo-bind\t` pin (`do-bind-arrow`), and this suite
  defers to it.

In the table, `\t` stands for a tab character, as in the other compiler
suites; `expectations.json` holds the exact strings.

| Fixture | Increment | Requirement | Pinned | Precedent | Needs | Twin |
| --- | --- | --- | --- | --- | --- | --- |
| `choose-rigid` | poly-closures | agree | - | - | closures, fields, generics | - |
| `choose-result-chain` | poly-closures | agree | - | - | closures, fields, generics, nested-patterns | - |
| `bind-instance-chain` | poly-closures | agree | - | - | closures, fields, generics, nested-patterns, recursion | - |
| `bind-rigid-caller` | poly-closures | agree | - | - | closures, fields, generics | - |
| `generic-compose` | poly-closures | agree | - | - | closures, generics | - |
| `generic-capture` | poly-closures | agree | - | - | closures, generics | - |
| `generic-arrow-instances` | poly-closures | agree | - | - | closures, fields, generics | - |
| `curried-generic-continuation` | poly-closures | agree | - | - | closures, fields, generics | - |
| `rigid-closure-twice` | poly-closures | reject | `Invalid\tcheck\taffine-reuse\t` | closures `closure-call-twice` | closures, generics | `generic-compose` |
| `rigid-domain-mismatch` | poly-closures | reject | `Invalid\tcheck\ttype-mismatch\t` | generics `rigid-mismatch` | closures, generics | `generic-compose` |
| `rigid-capture-twice` | poly-closures | reject | `Invalid\tcheck\taffine-reuse\t` | closures `capture-affine-twice` | closures, fields, generics | `choose-rigid` |
| `rigid-reusable-type` | poly-closures | reject | `Invalid\tcheck\treusable-type\t` | generics `reusable-type-param` | closures, fields, generics | `choose-rigid` |
| `bind-arrow-instance` | poly-closures | reject | exit 2 | generics `kind-type-for-data` | closures, fields, generics, nested-patterns, recursion | `bind-instance-chain` |
| `choose-branch-mismatch` | poly-closures | reject | `Invalid\tcheck\ttype-mismatch\t` | generics `wrong-type-arg` | closures, fields, generics, nested-patterns | `choose-result-chain` |
| `bind-promoted-instance` | poly-closures | agree | - | - | closures, fields, generics | - |
| `promoted-affine-instance` | poly-closures | reject | `Invalid\tcheck\treusable-type\t` | closures `reusable-closure-binder` | closures, fields, generics | `bind-promoted-instance` |
| `rank2-pure-bind` | poly-closures | agree | - | - | closures, fields, generics, type-level-definition | - |
| `rank2-continuation` | poly-closures | agree | - | - | closures, fields, generics, type-level-definition | - |
| `rank2-partial-bind` | poly-closures | agree | - | - | closures, fields, generics, type-level-definition | - |
| `rank2-try` | poly-closures | agree | - | - | closures, fields, generics, nested-patterns, type-level-definition | - |
| `rank2-choose-action` | poly-closures | agree | - | - | closures, fields, generics, nested-patterns, type-level-definition | - |
| `rank2-two-answers` | poly-closures | agree | - | - | closures, fields, generics, type-level-definition | - |
| `rank2-param` | poly-closures | agree | - | - | closures, fields, generics | - |
| `rank2-do-block` | poly-closures | agree-or-unsupported | - | - | closures, do-notation, fields, generics, type-level-definition | - |
| `rank2-rigid-answer` | poly-closures | reject | `Invalid\tcheck\ttype-mismatch\t` | generics `rigid-mismatch` | closures, fields, generics, type-level-definition | `rank2-pure-bind` |
| `rank2-continuation-twice` | poly-closures | reject | `Invalid\tcheck\taffine-reuse\t` | closures `closure-call-twice` | closures, fields, generics, type-level-definition | `rank2-pure-bind` |
| `rank2-run-twice` | poly-closures | reject | `Invalid\tcheck\taffine-reuse\t` | closures `closure-call-twice` | closures, fields, generics, type-level-definition | `rank2-two-answers` |
| `rank2-monomorphic-arg` | poly-closures | reject | `Invalid\tcheck\ttype-mismatch\t` | closures `closure-domain-mismatch` | closures, fields, generics | `rank2-param` |
| `rank2-choose-mismatch` | poly-closures | reject | `Invalid\tcheck\ttype-mismatch\t` | generics `wrong-type-arg` | closures, fields, generics, nested-patterns, type-level-definition | `rank2-choose-action` |
| `kind-closure-list` | poly-closures | agree | - | - | closures, fields, generics, recursion | - |
| `kind-higher-order` | poly-closures | agree | - | - | closures, fields, generics | - |
| `kind-forward` | poly-closures | agree | - | - | closures, fields, generics, recursion | - |
| `kind-two-quantities` | poly-closures | agree | - | - | closures, fields, generics | - |
| `kind-result-list` | poly-closures | agree | - | - | closures, fields, generics, nested-patterns, recursion | - |
| `kind-zero-arrow` | poly-closures | agree | - | - | closures, fields, generics, recursion | - |
| `kind-closure-at-data` | poly-closures | reject | exit 2 | generics `kind-type-for-data` | closures, fields, generics, recursion | `kind-closure-list` |
| `kind-closure-reuse` | poly-closures | reject | `Invalid\tcheck\taffine-reuse\t` | closures `closure-call-twice` | closures, fields, generics, recursion | `kind-closure-list` |
| `kind-quantity-mismatch` | poly-closures | reject | `Invalid\tcheck\ttype-mismatch\t` | generics `quantity-invariant` | closures, fields, generics, recursion | `kind-forward` |
| `kind-reuse-affine-result` | poly-closures | reject | `Invalid\tcheck\treusable-type\t` | sugar `annotation-reusable-quantity` | closures, fields, generics, recursion | `kind-forward` |
| `kind-meet-reuse` | poly-closures | reject | `Invalid\tcheck\treusable-type\t` | generics `meet-not-reusable` | closures, fields, generics | `kind-two-quantities` |
| `template-map-types` | templates | agree | - | - | closures, fields, generics, recursion | - |
| `template-fold-quant` | templates | agree | - | - | closures, fields, generics, poly-closures, recursion | - |
| `template-any-forward` | templates | agree | - | - | closures, fields, generics, poly-closures, recursion | - |
| `template-set-known-thunk` | templates | agree | - | - | closures, fields, generics, nested-patterns, poly-closures, recursion | - |
| `template-filter-data` | templates | agree | - | - | closures, fields, generics, recursion | - |
| `template-generic-arg` | templates | agree | - | - | closures, fields, generics, poly-closures, recursion | - |
| `template-open-type` | templates | reject | exit 2 | sugar `template-open-argument` | closures, fields, generics, recursion | `template-map-types` |
| `template-type-mismatch` | templates | reject | `Invalid\tcheck\ttype-mismatch\t` | closures `closure-domain-mismatch` | closures, fields, generics, recursion | `template-map-types` |
| `template-quant-kind` | templates | reject | exit 2 | generics `kind-type-for-data` | closures, fields, generics, poly-closures, recursion | `template-fold-quant` |
| `template-plain-param` | templates | reject | exit 2 | sugar `template-forward` | closures, fields, generics, recursion | `template-map-types` |
| `template-thunk-affine` | templates | reject | `Invalid\tcheck\taffine-reuse\t` | closures `capture-then-use` | closures, fields, generics, nested-patterns, poly-closures, recursion | `template-set-known-thunk` |
| `sigma-pair` | templates | agree | - | - | closures, destructuring-let, fields, generics, poly-closures, type-level-definition | - |
| `sigma-dependent` | templates | agree | - | - | fields, generics, nested-patterns, type-level-definition | - |
| `sigma-unpack` | templates | agree | - | - | closures, destructuring-let, fields, generics, poly-closures, type-level-definition | - |
| `sigma-reusable` | templates | agree | - | - | fields, generics | - |
| `sigma-in-result-action` | templates | agree | - | - | closures, destructuring-let, fields, generics, nested-patterns, poly-closures, type-level-definition | - |
| `sigma-snd-mismatch` | templates | reject | `Invalid\tcheck\ttype-mismatch\t` | generics `wrong-type-arg` | fields, generics, nested-patterns, type-level-definition | `sigma-dependent` |
| `sigma-unrefined` | templates | reject | exit 2 | - | fields, generics, nested-patterns, type-level-definition | `sigma-dependent` |
| `sigma-family-live-binder` | templates | reject | exit 2 | - | fields, generics, nested-patterns, type-level-definition | `sigma-dependent` |
| `sigma-affine-twice` | templates | reject | `Invalid\tcheck\taffine-reuse\t` | sugar `tuple-affine-reuse` | closures, destructuring-let, fields, generics, poly-closures, type-level-definition | `sigma-pair` |
| `sigma-reuse-affine` | templates | reject | `Invalid\tcheck\treusable-type\t` | sugar `annotation-reusable-quantity` | fields, generics | `sigma-reusable` |

## Needs and blocking

The **Needs** column lists capabilities outside the owning increment (`needs`
in `expectations.json`):

- `fields`: fielded constructors, checked and evaluated today.
- `recursion`: first-parameter structural recursion (increment 1, landed).
  Every self-call passes the descent rule, including those inside a
  continuation lambda (`bind-instance-chain`, `ordinals`) and those that
  forward `~` or quantity arguments unchanged before a smaller field.
- `nested-patterns`: constructor patterns inside constructor patterns, and
  wildcards (increment 3, nest).
- `generics`: generic datatypes, erased type parameters and quantity arguments
  (increment 6).
- `closures`: monomorphic lambdas, arrow-typed parameters and function values
  (increment 7). This suite lifts the monomorphic limit, so every
  `poly-closures` fixture needs increment 7's machinery first.
- `destructuring-let`: a destructuring let of a constructor, `Pack{a,b} = p`.
  It is how this suite spells `(a,b) = pair` (`src/driver.bend:45`,
  `packages/vec/main.bend:98`) on its own Sigma, without Base. `sugar-check`
  owns the form (sugar `destructure-constructor`). Until it lands, Knot reports
  `Unsupported\tparse\tdestructuring-binding\t` (`src/parse.bend:134`), so
  `sigma-pair`, `sigma-unpack`, `sigma-in-result-action` and
  `sigma-affine-twice` stay blocked. The last one pins `affine-reuse` on a `g`
  that the let binds.
- `type-level-definition`: a def whose result is a type. This covers
  `Act(A)` (the `IO(A)` shape), `Both(A,B)` (the `Pair` shape) and `Shade(f)`, a
  family that computes by `match`. The generics suite lists this capability as
  outside increment 6, and baseslice claims `Pair`. `poly-closures` cannot
  deliver higher-rank `IO(A)` without it, so whichever of `poly-closures`,
  `templates` or baseslice lands first supplies it for the others.
- `do-notation`: statement-only `do` desugaring (`rank2-do-block` only). The
  io suite requires it `agree` over IO for `io-check`. No suite requires it
  over another monad. The sugar suite has no `do` fixture.
- `poly-closures`: a `templates` fixture that also builds, stores or applies a
  closure at a generic or erased-type position:
  - `template-set-known-thunk` and `template-thunk-affine` run a choose thunk at
    `Opt<&2,Term>`;
  - `template-fold-quant`, `template-quant-kind` and `template-any-forward`
    fold a `Seq<&1,Flag -> Flag>` of closures;
  - `template-generic-arg` passes `ident(Flag)` as a function value;
  - `sigma-pair` and `sigma-affine-twice` store a closure in a pair component;
  - `sigma-unpack` applies `f: A -> B -> R`;
  - `sigma-in-result-action` binds a rank-2 action at a pair type and passes a
    partial `read_pair(depth)`.

A fixture is blocked while a need it names is unavailable. The runner reports a
blocked fixture separately. It never relabels a blocked fixture as passing, and
never re-expects one.

The `templates` increment can pass three seed-valid fixtures before
`poly-closures`, `sugar-check` or any type-level definition lands:
`template-map-types`, `template-filter-data` and `sigma-reusable`. The
negatives next to them are `template-open-type`, `template-type-mismatch`,
`template-plain-param` and `sigma-reuse-affine`. These isolate the `~`
mechanics, type binders and the Sigma quantity rule from polymorphic closures.

The Sigma fixtures also use the family machinery that declares a Sigma: an
erased parameter of arrow kind (`-B: @-x: A -> Kind(b)`), a dependent field
type (`snd: B(fst)`) and its refinement by `match`, and a type-level lambda
passed as a type argument (`_ => Color`, `x => Shade(x)`). No need names it,
because `templates` owns it (`increments.templates` in `expectations.json`).
Only the sigma fixtures use it, and Sigma is the form `templates` delivers.
The closures suite's unowned need `dependent-function-types` names a
different form: a term-level arrow `@-A: Type -> A -> A`. `poly-closures`
takes that one (`rank2-param`).

## Existing assertions this suite supersedes

D7 keeps existing assertions unchanged, so these are recorded here and not
edited. Each needs a reviewed superseding amendment, or selection by a separate
profile, when the owning increment lands:

- `tests/compiler-generics`:
  - `closure-apply` pins `Unsupported\tparse\tparameter-type\t` for
    `apply(-A: Type, -B: Type, f: A -> B, x: A)`. `generic-arrow-instances`
    uses the same `apply` and requires `agree`. The VM design already marks
    this pin for revisiting by `poly-closures`.
  - `template-twice` pins `Unsupported\tparse\ttemplate-binder\t`. Every
    `templates` fixture here requires `agree`.
- `tests/compiler-closures`:
  - `template-map` pins `Unsupported\tparse\ttemplate-binder\t` for a `~f`
    binder. `template-map-types` requires `agree` for the same form with type
    binders.
  - `dependent-arrow` is `agree-or-unsupported` for `f: @-A: Type -> A -> A`.
    `rank2-param` requires `agree` for that parameter type. `agree` satisfies
    the closures pin, so nothing there changes, but `poly-closures` may no
    longer answer `Unsupported`.
  - The VM design records that campaign/closures defunctionalizes
    monomorphically per arrow type. Every `generic-arrows` fixture needs that
    limit lifted.
- The template-binder pins that the sugar suite lists under the same heading:
  - `tests/subsets/classification-cases.json`: `template.bend` and
    `template-leading-pair.bend` pin `Unsupported\tparse\ttemplate-binder\t`.
  - `src/LAWS.bend`: the `template_binder` law. It quantifies over every suffix,
    so supporting templates falsifies it as stated. Replacing it is a
    coordinator or user decision, and it must be made before implementation.
- The destructuring pins that the sugar suite lists under the same heading.
  `sigma-pair`, `sigma-unpack` and `sigma-affine-twice` write `Pack{..} = p`
  and need `destructuring-let`, so `sugar-check` supersedes these, not this
  suite. They are listed so that neither side misses them:
  - `tests/subsets/classification-cases.json`: `destructure.bend` pins
    `Unsupported\tparse\tdestructuring-binding\t` for `Cell{value} = x`;
  - `src/LAWS.bend`: the `destructuring_binding` law, which states that prefix
    is `Unsupported` for every suffix.
- The generic-datatype and type-application pins in
  `tests/subsets/classification-cases.json`. Every fixture here declares a
  generic datatype and applies it in parameters, results and typed lets
  (`curried-generic-continuation.bend:49`, `sigma-reusable.bend:31`,
  `sigma-reuse-affine.bend:39`). If generics has not already superseded these
  pins when `poly-closures` or `templates` lands, that increment must:
  - `generic.bend`: `Unsupported\tparse\tgeneric-datatype\t`;
  - `application-parameter.bend`: `Unsupported\tparse\tparameter-type\t`;
  - `application-return.bend` and `application-binding.bend`:
    `Unsupported\tparse\ttype-application\t`;
  - `application-parameter-after-prefix.bend`,
    `application-return-after-prefix.bend` and
    `application-binding-after-prefix.bend`. These are seed-invalid programs
    whose malformed type application (`List<)`, `List<:`, `List< =`) comes after
    the prefix, so Knot pins them `Unsupported`. Once Knot parses type
    applications, it reaches the malformation. Its answer then becomes that
    later error, an `Invalid`, rather than the pinned `Unsupported`.

## Open questions for the coordinator

These findings came out of the suite's audit. They cross increment
boundaries, so this suite records them and does not decide them:

- **Statement-only `do` before `vm-e2e2`.** `vm-e2e2` compiles `parse-cli`,
  which has a `do IO<Unit>:` block at `src/parse-cli.bend:27`. It depends on
  `sugar-check`, `poly-closures`, `templates` and `baseslice-check`, but not on
  `io-check`, the only increment whose suite requires that block `agree`.
  Every suite gating the four prerequisites either pins `do` as
  `agree-or-unsupported` (closures `do-block`, baseslice `io-do-sequence`,
  `rank2-do-block` here) or has no `do` fixture (sugar). One of these is
  needed: `io-check` (or a statement-only `do` desugaring) becomes a
  prerequisite of `vm-e2e2`, or `sugar-check` takes statement-only `do` with a
  frozen `agree` fixture.
- **Data types that recur through their own generic instance.** Knot's AST
  types are declared this way: `syntax.Node` (`arguments: List<&2,Node>`),
  `core.Term` (`List<&2,Term>`), `core.Binding` (`known: Maybe<&2,Term>`) and
  `eval.Value` (`List<&2,Value>`). No suite has such a fixture. The audit's seed
  probe of a `Node is Data` with `Seq<&2,Node>` and `Opt<&2,Node>` fields
  checks and runs. A `Seq<&1,Node>` field is refused
  (`expected : Data`, `observed : Type`). The form is a datatype kind rule, so
  it belongs to `generics` or `fields`, not to `poly-closures` or
  `templates`. This suite does not add it. An owner needs to add the
  positive and negative pair.

## Overlaps with other suites

- **Closures (increment 7).** That suite owns monomorphic closures, including
  `generic-choose-bind`, which instantiates `choose` at `Color` and at
  `Flag -> Flag`. Here `choose` runs at the caller's rigid `A`, at
  two-quantity instances and at the rank-2 `Act(Color)`, and `bind` at
  `Seq<&2,Flag>` and `Tree`. Closures' `+` lambda binders are at an enum
  (`lambda-reusable-binder`) or an arrow (`reusable-closure-binder`). Here they
  are at a generic instance (`bind-promoted-instance`). Negatives reuse
  closures' codes and add nothing to its vocabulary.
- **Generics (increment 6).** That suite owns `Kind(a)` over data and `Box`
  values, `quantity-zero` with data, and the quantity meet over a data pair.
  Here the element types are arrows (`kind-closure-list`, `kind-zero-arrow`),
  results (`kind-result-list`) and closure payloads under a meet
  (`kind-two-quantities`).
- **Sugar.** That suite owns the `set_all` template (`template-set-known`),
  the template mechanics without generics, and `(a,b)` tuple sugar over Base
  `Pair`. Here the template is the exact `set_known` body, with a choose thunk
  and a nested `+` pattern. The type and quantity binders are those of Base's
  `List.map`, `List.foldl`, `List.any` and `List.filter`. The Sigma is a
  fixture datatype, destructured by constructor patterns and lets, so that no
  sugar resolves to Base.
- **Baseslice (increment 8).** It checks Base's own `IO`, `Pair` and `Sigma`
  declarations. This suite reproduces those shapes without Base, so each
  increment can be qualified on its own.

## Seed behaviours this suite freezes

These behaviours were observed while writing the suite. They are recorded
because an implementer could reasonably expect otherwise.

- **Generic arrows.**
  - A closure at a rigid arrow is still affine (`rigid-closure-twice`).
    Captures of a rigid `A: Type` cannot be shared, and a `+` binder at such an
    `A` is refused (`rigid-capture-twice`, `rigid-reusable-type`).
  - A `-A: Data` parameter refuses an arrow instance (`bind-arrow-instance`).
    The same program with `-A: Type` checks and runs.
  - A type argument may itself be an arrow into an instance
    (`generic-arrow-instances`), and a generic `compose` may be passed to
    `compose` (`generic-compose`).
  - A `+` lambda binder at a generic instance follows the parameter rule. It is
    accepted at `Seq<&2,Flag>`, on a first or a second curried binder
    (`bind-promoted-instance`). It is refused at `Seq<&1,Flag>`, with the
    error at the binder (`promoted-affine-instance`).
- **Higher rank.**
  - `Act(A)` unfolds to a rank-2 arrow, so an action is applied directly to its
    answer type and continuation, as in `m(Color,c => Emit{c})` or
    `load(f,next,Color,k)`. `Act.bind` over-applies `f(x,R,k)`.
  - The answer type is rigid inside `R => k => ..` (`rank2-rigid-answer`).
  - The seed's polymorphism is impredicative: `Act(Act(Flag))` and
    `Act.join` check (`rank2-two-answers`). Knot's source relies on it for
    `S.choose(IO(Unit),..)`, and `choose(Act(Color),..)` checks
    (`rank2-choose-action`). A thunk at `Act(Flag)` there is a mismatch
    between the unfolded arrows,
    `@-R:Type -> @k:(@_:Color -> Op<R>) -> Op<R>` against its `Flag`
    counterpart (`rank2-choose-mismatch`).
  - A named generic def fits a rank-2 parameter (`ident` for
    `@-A: Type -> A -> A`). A monomorphic def does not
    (`rank2-monomorphic-arg`).
  - A generic def applied to its erased type argument alone is a function
    value: `Act.pass(A)` is the `f` of `Act.bind` (`rank2-try`, as in
    `IO.try`).
  - An action is an affine closure. Running one twice, even at two different
    answer types, is reuse (`rank2-run-twice`).
  - `Act.die` drops its continuation, and a bind after it never runs its `f`
    (`rank2-pure-bind`, `chain(Off{},..)`).
- **Kind(a).**
  - An arrow is `Type`, so it instantiates `Kind(&1)`
    (`kind-closure-list`), not `Kind(&2)` (`kind-closure-at-data`).
  - `Kind(&0)` admits an arrow, and closures stored at `&0` may be built live
    and never called (`kind-zero-arrow`).
  - The explicit quantity argument fixes the instance: `rev(&2,Flag,xs)` refuses
    a `Seq<&1,Flag>` (`kind-quantity-mismatch`).
  - `Res<Fault,A>` is `Res<&1,&1,Fault,A>`. The seed accepts the short form
    where the long one is spelled (`kind-two-quantities`), and prints the long
    form in its diagnostics (`choose-branch-mismatch`).
- **Templates.**
  - A `~` binder may be passed on as the erased type argument of a plain
    generic def (`template-filter-data`, `put(A,..)`).
  - A closed `~` lambda may mention the enclosing template's own `~f`
    (`template-any-forward`, `all`). It may also mention generic defs at
    explicit types, including a partial application such as `~ident(Flag)`
    (`template-generic-arg`).
  - A caller's erased type variable is not comptime (`template-open-type`).
  - `~` before an argument of a plain def is a parse error
    (`template-plain-param`).
  - Without `+payload`, `set_known` is rejected: the thunk captures `payload`
    and the self-call passes it (`template-thunk-affine`).
- **Sigma.**
  - The family parameter wants an erased binder. `x => Shade(x)` fits, but the
    def `Shade` with a live binder does not (`sigma-family-live-binder`).
  - A match on `fst` refines the type of `snd` in each arm (`sigma-dependent`).
    Without it, `snd` has the stuck type `Shade(f)` (`sigma-unrefined`).
  - `Dep<&2,&2,..>` is `Data`, and `Dep<&1,&1,..>` is not
    (`sigma-reusable`, `sigma-reuse-affine`).
  - A Sigma may be the error of a `Res`, which may be the answer of an action.
    `case Fail{Pack{code,message}}` nests a `Pack` pattern in `Fail`, and
    `Act.bind` accepts a partial `read_pair(depth)` at the pair type
    (`sigma-in-result-action`).
- These probes are not frozen, but they shaped the fixtures:
  - A let of a bare constructor needs an annotation: `+blank = Blank{}` reports
    `cannot infer`, and `+blank : Mode = Blank{}` checks.
  - Matching a later parameter after an earlier one is accepted. Matching an
    earlier parameter inside the arms of a later one is refused, so `render`
    and `lookup` take the matched value first.
  - Calling a def declared below from a live body is refused ("a filled
    definition"), so helpers precede their callers.
  - A `do` statement desugars as `Unit <- statement`. Without a `Unit` type in
    scope the seed refuses the block (`expected : a defined name`,
    `observed : Unit`), so `rank2-do-block` declares its own `Unit`.
- Tags come from a syntactic reading of each fixture's enum declarations, in
  declaration order. The seed only names the constructor.

## What the implementers must wire

The gate runner, its receipts and the build lanes belong to the implementers.
Follow the pattern of `tests/compiler-fields/check.py`.

1. Run `regen.py` first. It is the seed lane: fixture hashes, seed hashes and
   all observations must still match before anything else counts.
2. Select the cases whose `increment` is yours. Build the check and eval CLIs,
   and the image and VM lanes once they exist. Check every selected fixture
   that is not blocked.
3. For `agree` fixtures, take each call in `observations`:
   - Evaluate `eval-cli <fixture> <entry> <budget> <ordinals...>`. It must
     yield `result.constructor`.
   - On each image or VM lane that exists, the same call must return
     `result.tag`.
   - `ordinals` are the live enum arguments in parameter order. Every entry here
     has only live enum parameters. Erased, template, function and rank-2
     parameters of internal definitions never cross the host boundary.
4. For `agree-or-unsupported` and `reject` fixtures, apply the requirement
   table to every CLI phase that runs, including eval and compile.
5. Report blocked fixtures (see Needs) separately from passes and failures.
6. Land the reviewed amendments listed under "Existing assertions this suite
   supersedes" in the same change, with their own review.

## Limits

- The seed lane is the reference interpreter. No seed-compiled binary is compared.
- A seed-invalid fixture records only its direct rejection, because a wrapper
  cannot import an invalid module.
- The suite pins behaviour on finite programs. It proves no checker property,
  no parametricity result and no soundness of the rank-2 encoding.
- Entries are observed only through the enum host boundary. Closures, actions,
  template instances and pairs never cross it, so their representations are
  checked only through the enum results they determine.
- Mirrors cite the source as it stands at this suite's base. Later edits to
  `src/` do not invalidate the fixtures, and `regen.py` does not re-read the
  cited lines.
- Continuations stay short: at most three list elements and four chained
  chooses. The suite does not measure stack depth, allocation or the cost of
  polymorphic dispatch; that belongs to the VM benchmarks.

## Census coverage

The goal of `poly-fixtures` is to cover every shape that S's census lists
under `generics`, `higher-order`, `templates` and `dependent`. This table
covers every declaration of Knot's source (see Scope) in those classes and in
`function-values` and `calls.partial`, 43 in all:
- In non-law `src/` files: all 25 `higher-order` declarations, all 3
  `templates` declarations, the 10 non-law `dependent` declarations, the 4
  `function-values` declarations and the 4 `calls.partial` declarations. That
  is 42 declarations.
- In the bytes package: its one `higher-order` declaration, `guard`.

Law and proof files are out of scope (see Scope). Fixture names without a
suite are in this suite.

| Declaration | Census classes | Covered by |
| --- | --- | --- |
| `0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend:29` guard (`packages/output_builder/bytes.bend:29`) | higher-order | `choose-result-chain` (thunks `Unit -> Res<Fault,State>`); closures `choose-thunks`. `next: Unit -> Result<Error,U32>` is a monomorphic thunk. |
| `src/catalog.bend:50` constructor_next | higher-order | `choose-result-chain` (thunks `Unit -> Res<Fault,State>`); closures `choose-thunks` |
| `src/check-cli.bend:39` opened | calls.partial | `rank2-partial-bind` (`opened(depth)`) |
| `src/check-cli.bend:45` open_source | calls.partial | `rank2-partial-bind` |
| `src/check-cli.bend:64` main | function-values | `rank2-partial-bind` (`arguments` as the `f` of a bind) |
| `src/check.bend:51` constructor | higher-order | `choose-result-chain`; closures `choose-thunks` |
| `src/check.bend:58` variable | higher-order | `curried-generic-continuation` |
| `src/check.bend:141` call_body | higher-order | `curried-generic-continuation` (a continuation over `Seq<&2,Flag>`) |
| `src/check.bend:147` binding_body | higher-order | `curried-generic-continuation` (`add`, `next: Scope -> ..`) |
| `src/check.bend:153` match_body | higher-order | `curried-generic-continuation` |
| `src/check.bend:161` arm_body | higher-order | `curried-generic-continuation` (`open`) |
| `src/check.bend:165` arm_scope | higher-order | `curried-generic-continuation` (`open`); `bind-promoted-instance` (`bound => +fs =>`, the `+fields` binder of `check.bend:211`) |
| `src/compile-cli.bend:62` main | function-values | `rank2-partial-bind` |
| `src/core.bend:35` invalid | dependent | sugar `dependent-result` |
| `src/core.bend:37` unsupported | dependent | sugar `dependent-result` |
| `src/core.bend:39` exhausted | dependent | `curried-generic-continuation` (`exhausted(-A: Type)`); sugar `dependent-result` |
| `src/core.bend:41` internal | dependent | sugar `dependent-result` |
| `src/driver.bend:15` checked | higher-order | `rank2-continuation` |
| `src/driver.bend:25` parsed | higher-order | `bind-instance-chain`, `rank2-continuation` |
| `src/driver.bend:30` source | higher-order | `bind-instance-chain` |
| `src/driver.bend:39` read_result | higher-order | `rank2-try`, `rank2-continuation` |
| `src/driver.bend:44` read_pair | higher-order | `rank2-do-block` (boundary), `sigma-pair`, `sigma-in-result-action` |
| `src/driver.bend:50` opened | higher-order | `rank2-continuation`, `rank2-partial-bind`, `sigma-in-result-action` |
| `src/driver.bend:55` load | higher-order | `rank2-continuation` |
| `src/eval-cli.bend:36` main | function-values | `rank2-partial-bind` |
| `src/eval.bend:23` internal | dependent | sugar `dependent-result` |
| `src/eval.bend:26` host | dependent | sugar `dependent-result` |
| `src/eval.bend:90` host_argument | higher-order | `curried-generic-continuation` |
| `src/parse-cli.bend:31` opened | calls.partial | `rank2-partial-bind` |
| `src/parse-cli.bend:37` open_source | calls.partial | `rank2-partial-bind` |
| `src/parse-cli.bend:56` main | function-values | `rank2-partial-bind` |
| `src/parse.bend:43` then | higher-order | `curried-generic-continuation` (`open`) |
| `src/patterns.bend:14` add | higher-order | `curried-generic-continuation` (`add`) |
| `src/patterns.bend:21` binder | higher-order | `curried-generic-continuation` (a two-argument curried continuation) |
| `src/scope.bend:77` set_known | higher-order, templates, dependent | `template-set-known-thunk`; sugar `template-set-known` |
| `src/scope.bend:85` refine | templates | `template-set-known-thunk` |
| `src/scope.bend:108` replace | templates | `template-set-known-thunk` |
| `src/syntax.bend:76` choose | higher-order, dependent | `choose-rigid`, `choose-result-chain`, `rank2-choose-action`; sugar `dependent-choose`; closures `generic-choose-bind` |
| `src/syntax.bend:81` bind | higher-order, dependent | `bind-instance-chain`, `bind-rigid-caller`, `bind-promoted-instance`, `kind-result-list`; sugar `dependent-bind` |
| `src/wasm.bend:55` internal | dependent | sugar `dependent-result` |
| `src/wasm.bend:100` call_body | higher-order | `curried-generic-continuation` |
| `src/wasm.bend:104` after_argument | higher-order | `curried-generic-continuation` |
| `src/wasm.bend:108` after_initializer | higher-order | `curried-generic-continuation` |

`generics` (380 declarations) and `quantities.arguments` (379) are type
applications. `quantities.polymorphic` is empty in `src/`: Knot declares no
`Kind(a)` parameter of its own. It reaches Base's `List.length`, `List.append`,
`List.reverse` and `List.reverse.go` instead, which `kind-closure-list` and
`kind-forward` mirror. A grep of non-law `src/` at this base finds these
type-application spellings, counted by occurrence:
- `List<&2,T>` (397);
- `Result<S.Error,T>` (327), the short form of `Result<&1,&1,S.Error,T>`;
- `Maybe<&2,T>` (32);
- `Result<&1,&1,..>` (20);
- `List<String>` (9), short for `List<&1,String>`;
- `Result<Error,A>` (3, in `syntax.bend`), `List<&1,T>` (2) and `Result<B.Error,..>` (1);
- `IO<Unit>` in `do` headers (4).

The fixtures write each spelling on their own carriers:
- `Seq<&2,Flag>` for `List<&2,T>`;
- `Res<Fault,A>` for the short `Result`, and `Res<&1,&1,Fault,Flag>` for the
  long one (`kind-two-quantities` passes the short form where the long one is
  spelled). The long form with a Sigma error, as the source writes it, is
  `Res<&1,&1,Both(Code,Flag),Color>` (`sigma-in-result-action`);
- `Opt<&2,Term>` for `Maybe<&2,T>`;
- `Seq<Flag>` for `List<String>`;
- `Seq<&1,Res<Fault,Flag>>` for `List<&1,T>`;
- `do Act<Color>` for `do IO<Unit>`.

**Census packages outside Knot's source.** Of the package modules that the
census scans and no `src/` file imports, four have declarations in these
classes: `int_map`, `symbols`, `term_store` and `vec`. `vec` is also scanned
as its published copy (`0xd684886d10b431b9dce6c3b2d1ef1980`). No fixture is
required for them:
- `term_store` (41) and `vec` (34, and the same 34 in the published copy): all
  `dependent`, meaning a type mentions an earlier erased parameter. The
  exception is `vec`'s `unpack` (`packages/vec/main.bend:97`), which is also
  `higher-order`. `sigma-unpack` mirrors it anyway.
- `symbols`: `Trie.rejoin` (`packages/symbols/main.bend:35`), a monomorphic
  `context: Trie -> Trie` applied inside a Base pair. That is closures plus
  sugar tuples.
- `int_map` (20): 13 are `dependent` only. The other seven are templates:
  `edit_path`, `set_path`, `remove_path`, `IntMap.fold`, `combine_value`,
  `union_step` and `IntMap.union_with` (`packages/int_map/main.bend:44-107`). `edit_path` takes a template binder
  of rank-2 type, `~join: @-T: Data -> IntMap<T> -> IntMap<T> -> IntMap<T>`.
  `set_path` feeds it the type lambda `~(T => lo => hi => Branch{lo,hi})`, and
  `remove_path` feeds it the generic def `~branch`. The audit's seed probe of
  that shape checks and runs. No suite has a fixture for it. If Knot's source
  comes to import `int_map`, it is the one shape here that no suite covers.

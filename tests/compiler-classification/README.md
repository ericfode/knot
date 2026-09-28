# Classification precision: classify-2

This increment repairs classification at three parser boundaries. It adds no
executable source capability. Expectations were fixed from the pinned seed and
literal source locations before editing `src/parse.bend`.

- A parameter tail is reachable only after an ordinary binder: leading template
  recognition already stops with Unsupported. A later `~` is therefore
  `Invalid parse parameter`, including after erased and reusable parameters.
- A constructor followed by `=` recognizes a destructuring binding only when the
  next token is neither `=` nor `>`. Both operators retain
  `Invalid parse end-of-body`.
- A named type followed by `<` is Unsupported before its generic declaration.
  Parameter types already use `parameter-type`; preserving that code retains the
  existing broader parameter-type boundary. Return types and local annotations
  now use `type-application`, located at `<`.

The parser edits are confined to `reply`, `ListTail`, `FunctionTail` and
`AnnotatedBinding`. `MatchTail` and import parsing are unchanged.

## Frozen controls and proof boundary

`tests/subsets/classification-cases.json` appends 17 cases, each with the seed
command, full stdout/stderr, exit, source hash, and literal Knot diagnostic:

| Family | New controls |
| --- | --- |
| Template binders | ordinary/erased/reusable non-leading binders; malformed non-leading type; two leading binders; malformed type after a leading prefix |
| Constructor bindings | `==` and `=>`, each with and without a right operand; malformed suffix after plain `=` |
| Type applications | parameter, return and local annotation; each with a malformed argument after `<` |

The four successful seed controls evaluate to `On{}`, `On{}`, `[]`, and `On{}`
(leading pair, parameter, return and local annotation respectively). Thirteen
controls are seed syntax errors. A recognized Unsupported prefix does not assert
that its remaining source is valid. The five malformed-after-prefix controls
exercise this boundary; malformed non-leading binders and operator expressions
remain Invalid.

`receipts/baseline.json` records the initial parser hash, commit and frozen
manifest hash. The baseline misses 12 of these 17 exact observations. Existing
fixture assertions are unchanged.

`src/PROOF.bend` checks all 16 frontend laws. Six are new: non-leading templates,
equality/arrow exclusion, and parameter/return/binding type applications. The
destructuring law now assumes its remaining token list starts with neither `=`
nor `>`; its rewrite proof fills that conditional law. Its premise is inhabited
by the original `destructure.bend` fixture's `x` token after `=` (and by an empty
token list). The other new laws quantify over arbitrary locations and suffixes.
These are parser transition laws, not whole-parser soundness or feature support.

## Gates

```sh
export BEND_NO_TELEMETRY=1
python3 tests/compiler-classification/check.py
python3 tests/subsets/check_frontend.py
npm run -s gates
npm run -s gates:verify
```

The new `classification` gate is appended to the existing fourteen gates. It
replays all 17 exact seed outputs and parser observations and kills six
parseable, type-correct semantic mutants: re-enable non-leading templates,
recognize equality as binding, recognize arrow as binding, and misclassify each
of the three type application positions as Invalid. Every kill requires the
specific wrong classification and unchanged source location; build failures,
timeouts and host failures cannot count as kills.

**After the generics supersession.** Generics parses `Name<...>` in all three
positions, which removed the two `type-application` anchors. The gate now
kills seven mutants, each on frozen witnesses from the classification
manifest:

| Mutant | File | Witnesses | Kill |
| --- | --- | --- | --- |
| `nonleading-template`, `equality-as-binding`, `arrow-as-binding` | `parse.bend` | unchanged | unchanged |
| `parameter-application-invalid` | `parse.bend` | `function-parameter` (generics) | `Invalid parse parameter-type` at the witness span |
| `type-expression-invalid` | `type-parse.bend` | the three `application-*-after-prefix` twins | `Invalid parse type-expression` at each twin's span |
| `return-application-untyped` | `parse.bend` | `application-return` | `Invalid parse function-result 46:47:5:11` instead of `Parsed` |
| `binding-application-untyped` | `parse.bend` | `application-binding` | `Invalid parse expected-= 65:66:6:10` instead of `Parsed` |

The parameter mutant keeps its original anchor, `unsupported(rest,"parameter-type")`;
only its witness moved, as in the frontend gate's `parameter-type-invalid`.
The last two break the routes from a result type and a local annotation into
the type grammar, so a seed-valid application is reported Invalid. Every
witness's frozen hash and unmutated parser outcome are checked first.

The unchanged frontend harness additionally checks all 29 classification cases
in native and Bun parser, checker, evaluator and compiler lanes. Its 174
downstream rejection observations include 58 compiler failures preserving an
existing output. No evaluator value or Wasm execution is claimed for Unsupported
or Invalid programs. The existing accepted program differential gates remain
the execution controls.

On the generics branch that paragraph describes main, not the current
harness. Generics changed the harness in `5eea108`: it now reads per-phase
expectations. It checks 30 cases, adding the `function-parameter` witness, and
reports 180 downstream phase observations. The generics
[assertion ledger](../compiler-generics/ASSERTION-CHANGES.md) lists every
change to this gate and the frontend gate.

Fresh precision evidence belongs to this increment. Existing frontend and other
shared receipts are left for the coordinator to refresh after merging.

## Limits and handoff

Templates, destructuring bindings and generic type applications remain
unsupported. This does not validate suffixes after an unsupported prefix or add
generic checking/evaluation/emission. Multi-scrutinee matching and import-path
classification belong to the concurrent nest and modules increments.

Offline Perch preflight checks structural review coverage; it supplies no style
ratings or semantic review. The coordinator owns live review and integration.

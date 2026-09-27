# Driver pipeline acceptance packet

Scope: the public `checked`, `parsed`, `source` entry points, new `parsed_root`
projection and unchanged `load` boundary in `src/driver.bend`. Fixed contract:
[SPEC.md](../../../src/style-campaign/compiler-pipeline-1/SPEC.md). Frozen inputs: [freeze.json](../../../src/style-campaign/compiler-pipeline-1/freeze.json). Candidate:
`4641537cb3b8d82a63ff519007d43ba6efc4f4458e656c12c1b83186a5c72a15`.
One generation passed the first compiler check; no diagnostic retry occurred.

## Claims and their limits

No new theorem, axiom or proof body is introduced. Five unchanged complete
proof entry points (`PROOF`, `check-PROOF`, `runtime-PROOF`, `fields-PROOF`,
`catalog-PROOF`) returned `All terms check.` in the existing suites. These prove
their existing stated claims; they do not prove universal driver equivalence.
Driver preservation is supported by finite native/Bun observations, immutable
independent fixture expectations, source review and exact emitted-byte comparison.
Seed Bend 2.0.29 / `574b6d3`, its checker/native backend, Bun, Base IO and Node's
Wasm engine remain trust dependencies. Model judgments are advisory.

## Public observations

| Operation | Constructible success witness | Failure/boundary observation |
| --- | --- | --- |
| `checked` | An empty `C.Book`; output is exactly `Before`, `Next`, `After`. | Each of five explicit `S.Error` constructors retains status, message, location and stream; no `Next` or `After`. |
| `parsed` | An empty sequence plus one residual token, with zero character/parser fuel and positive checker fuel, invokes `Next` once. | An injected parse error wins even with zero checker fuel; a successful parse with zero checker fuel reports checker exhaustion. Residual tokens remain deliberately ignored. |
| `source` | Empty text and zero character fuel succeed with positive parser/checker fuel. | Existing Wasm integration covers separate character/parser/checker exhaustion, invalid and unsupported source; direct source witness fixes callback order. |
| `load` | Existing evaluator and compiler corpus traverses file open/read/close and the shared driver. | Existing fields suite includes six host probes; failed compilation and exhaustion do not create an artifact or overwrite the preserved output marker. |
| `parsed_root` | Its matched `P.Parsed` contains an inhabited syntax sequence and residual list. | It returns the root and deliberately discards the residual tokens; direct `parsed` witnesses observe the resulting public behavior. |

[witnesses.json](../../../src/style-campaign/compiler-pipeline-1/witnesses.json) fixes literal expectations before generation.
All ten cases pass in both native and Bun lanes before and after (20 observations
per revision). Each is a runtime example, not a quantified law. IO traces observe
order and multiplicity, not wall-clock timing. Existing source fixtures, expected
diagnostics, theorem statements and assertion bodies were unchanged.

The pipeline is stateless except for its final IO continuation. Fuel belongs to
the supplied stage, never to a shared counter. Independent tests preserve the
original complete compiler observations. Error precedence follows the explicit
`syntax.bind` Fail/Done cases and is exercised by the direct incoming-failure
witness. No new arithmetic, storage index, allocation policy or GPU reachability
is introduced. These categories impose no new driver-specific law in this diff.

## Deterministic evidence

All existing suites passed: frontend (14 fixtures, 24 boundaries, 4 mutants),
checker (49 fixtures, 98 observations, 10 depth/16 catalog-bound observations,
7 mutants), Wasm (25 programs, 90 independent calls in two lanes, 64 rejection
pairs, 44 boundaries, 7 mutants), fields (40 fixtures, 240 phase observations,
36 budgets, 6 host probes, 12 level/inspection observations, 9 mutants), and
structural catalog (16 fixtures, 4 boundary pairs, 7 mutants).

Their 34 existing mutants first parse/type-check and then violate unchanged
observations. No new driver-specific mutant was introduced, and the existing
mutation coverage must not be described as exhaustive driver equivalence.
Complete machine records are the `receipts/candidate-*.json` files. The launcher
redirects build/receipt destinations only, preserving each test module's code.
The 25 Wasm modules emitted by the candidate match the fresh baseline byte for
byte. This is finite artifact equality, not a performance or bootstrap result.

Targeted semantic review ran four rules on each changed declaration, 12 completed
checks with no reported findings. The `parsed` and `source` dependency contexts
were truncated. Compression/delight ratings meet their targets, but memetic
ratings do not; normal composition review is unavailable. The supplementary
packet assumes explicit opaque stage interfaces and cannot supply an automatic
complete-composition pass. No review score licenses language acceptance.

## Coordinator context supplement

This review is anchored to accepted driver commit `c2045e3`. The original
zero-coverage attempt is retained in the owner evidence. Links are rebased;
the unchanged selected source, bind helper and fixed IO witnesses are supplied
here so this file-rule review does not depend on opening those links. Lexer,
parser and checker stage implementations are unchanged opaque dependencies.
This is a semantic acceptance-packet review, not a replacement style score.

### Exact selected source

```bend
type Limits is Data:
  Limits{characters: Nat, parser: Nat, checker: Nat}

def fail(+error: S.Error) -> IO(Unit):
  IO.die(Unit,D.status(error),D.error(error))

def checked(result: Result<S.Error,C.Book>, next: C.Book -> IO(Unit)) -> IO(Unit):
  match result:
    case Fail{error}: fail(error)
    case Done{book}: next(book)

# The public parsed entry checks only the root; residual tokens are ignored.
def parsed_root(value: P.Parsed) -> S.Node:
  match value:
    case P.Parsed{root,rest}: root

def parsed(limits: Limits, result: Result<S.Error,P.Parsed>, next: C.Book -> IO(Unit)) -> IO(Unit):
  match limits:
    case Limits{chars,parser,+checker}:
      checked(S.bind(P.Parsed,C.Book,result,tree => K.check(checker,parsed_root(tree))),next)

def source(+limits: Limits, text: String, next: C.Book -> IO(Unit)) -> IO(Unit):
  match limits:
    case Limits{chars,+parser,+checker}:
      checked(
        S.bind(List<&2,S.Token>,C.Book,L.tokenize(chars,text),tokens =>
          S.bind(P.Parsed,C.Book,P.parse(parser,tokens),tree =>
            K.check(checker,parsed_root(tree)))),
        next)
```

### Exact first-error combinator

```bend
def bind(-A: Data, -B: Data, result: Result<Error,A>, next: A -> Result<Error,B>) -> Result<Error,B>:
  match result:
    case Fail{e}: Fail{e}
    case Done{x}: next(x)
```

### Fixed independent direct IO cases

The runner emits `Before`, executes the call, then emits `After` on success.
Each literal expected record below was frozen before candidate generation.

```json
[
  {
    "name": "checked-invalid",
    "call": "D.checked(Fail{S.Invalid{\"parse\",\"sentinel\",S.At{7,9,2,3}}},book => IO.print(\"Next\"))",
    "expected": {
      "exit": 2,
      "stdout": "Before\n",
      "stderr": "Invalid\tparse\tsentinel\t7:9:2:3\n"
    }
  },
  {
    "name": "checked-unsupported",
    "call": "D.checked(Fail{S.Unsupported{\"lex\",\"sentinel\",S.At{7,9,2,3}}},book => IO.print(\"Next\"))",
    "expected": {
      "exit": 3,
      "stdout": "Before\n",
      "stderr": "Unsupported\tlex\tsentinel\t7:9:2:3\n"
    }
  },
  {
    "name": "checked-exhausted",
    "call": "D.checked(Fail{S.Exhausted{\"check\",S.At{7,9,2,3}}},book => IO.print(\"Next\"))",
    "expected": {
      "exit": 4,
      "stdout": "Before\n",
      "stderr": "Exhausted\tcheck\tbudget\t7:9:2:3\n"
    }
  },
  {
    "name": "checked-host",
    "call": "D.checked(Fail{S.Host{\"read\",\"sentinel\"}},book => IO.print(\"Next\"))",
    "expected": {
      "exit": 5,
      "stdout": "Before\n",
      "stderr": "HostFailure\tread\tsentinel\n"
    }
  },
  {
    "name": "checked-internal",
    "call": "D.checked(Fail{S.Internal{\"check\",\"sentinel\"}},book => IO.print(\"Next\"))",
    "expected": {
      "exit": 6,
      "stdout": "Before\n",
      "stderr": "InternalFailure\tcheck\tsentinel\n"
    }
  },
  {
    "name": "checked-success",
    "call": "D.checked(Done{C.Book{Nil{},Nil{}}},book => IO.print(\"Next\"))",
    "expected": {
      "exit": 0,
      "stdout": "Before\nNext\nAfter\n",
      "stderr": ""
    }
  },
  {
    "name": "parsed-first-failure",
    "call": "D.parsed(D.Limits{0n,0n,0n},Fail{S.Invalid{\"parse\",\"sentinel\",S.At{7,9,2,3}}},book => IO.print(\"Next\"))",
    "expected": {
      "exit": 2,
      "stdout": "Before\n",
      "stderr": "Invalid\tparse\tsentinel\t7:9:2:3\n"
    }
  },
  {
    "name": "parsed-checker-zero",
    "call": "D.parsed(D.Limits{0n,0n,0n},Done{P.Parsed{S.Sequence{Nil{}},Nil{}}},book => IO.print(\"Next\"))",
    "expected": {
      "exit": 4,
      "stdout": "Before\n",
      "stderr": "Exhausted\tcheck\tbudget\t0:0:0:0\n"
    }
  },
  {
    "name": "parsed-unused-budgets-and-rest",
    "call": "D.parsed(D.Limits{0n,0n,512n},Done{P.Parsed{S.Sequence{Nil{}},Con{S.Token{\"unconsumed\",S.At{7,9,2,3}},Nil{}}}},book => IO.print(\"Next\"))",
    "expected": {
      "exit": 0,
      "stdout": "Before\nNext\nAfter\n",
      "stderr": ""
    }
  },
  {
    "name": "source-empty",
    "call": "D.source(D.Limits{0n,512n,512n},\"\",book => IO.print(\"Next\"))",
    "expected": {
      "exit": 0,
      "stdout": "Before\nNext\nAfter\n",
      "stderr": ""
    }
  }
]
```

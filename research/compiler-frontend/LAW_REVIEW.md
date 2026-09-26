# Frontend boundary law review — 2026-09-26

Scope: lexer/parser checkpoint for Knot enum profile 1. No resolver, type/quantity
checker, evaluator or Wasm emitter is claimed here. `Parsed` is a syntax result;
all eight semantic negatives intentionally parse and are rejected only by the
pinned reference at this checkpoint. The complete active compiler milestone
still requires those missing components and source-to-Wasm execution.

## Contract and public observations

`lex.tokenize(fuel: Nat, input: String)` returns tokens with text and source
location, or Invalid/Unsupported/Exhausted. A token location contains start/end
scalar offsets, one-based line and zero-based column. Accepted source is ASCII,
so its scalar and byte offsets coincide. EOF is explicit and trailing names are
flushed. Comment/newline handling preserves locations and token order. Source
characters have a hard 65536 cap in `step` before counter increments; the CLI
reads 65537 bytes, preventing a truncated accepted ASCII prefix of a larger file.

`parse.parse(depth: Nat, tokens)` returns an explicit syntax tree and remaining
EOF, or structured failure. It parses enum declarations, typed function headers,
quantities, optional local type annotations, constructor/call arguments,
sequential bindings and nested constructor arms. Its one recursive `run` reduces
Nat fuel on every recursive invocation. This is a nesting/traversal-depth bound,
not a claim that depth equals total work. It never substitutes an empty success
for budget exhaustion. Identifier, delimiter and indentation checks are local
helpers. The parser does not decide semantic validity.

`diagnostic.tree` canonically observes names, order, quantities, annotations,
arguments and all branches of the syntax tree. It has its own explicit budget.
It is not the semantic evaluator. CLI defaults are 65536 source characters and
512 parser depth; optional decimal overrides are bounded by 65536/4096. Exit
codes 2/3/4/5/6 distinguish Invalid/Unsupported/Exhausted/HostFailure/InternalFailure.
Native and Bun parse the same physical source files and report the same trees.

## Actual laws and witnesses

`LAWS.bend` declares and `PROOF.bend` fills these four universal boundary laws:

1. For every `fuel: Nat`, `tokenize(fuel, "")` returns exactly
   `[Token{"<eof>",At{0,0,1,0}}]`. Witnesses include zero and positive fuel.
2. For every `extra: Nat`, `tokenize(1n+extra, "a")` returns exactly
   `[Token{"a",At{0,1,1,0}}, Token{"<eof>",At{1,1,1,1}}]`.
   Nonempty witness: `extra=0n`; increasing fuel remains covered.
3. For every `c: Char` and `tail: String`, `tokenize(0n,SCon{c,tail})` is
   `Fail{Exhausted{"lex",At{0,0,1,0}}}`. Witness `c='a', tail="b"` has
   nonempty pending input; this law does not assert that the input is invalid.
4. For every token list, `parse(0n,tokens)` is exactly
   `Fail{Exhausted{"parse",here(tokens)}}`. Witnesses: empty list and a list
   beginning with the `type` token from the Flag fixture.

The complete proof entry passes the pinned Bend 2.0.29 checker with
`All terms check.` No new axiom, `@unsafe`, hole or assumed body is introduced.
Proofs use case distinction/concrete reduction. These are universal over their
stated parameters, not universal lexing/parsing correctness proofs.

## API/evidence matrix and independent expectations

| Operation | Defining observations | Evidence | Omission |
| --- | --- | --- | --- |
| tokenize | text, order, EOF, exact offsets/lines/columns | four literal lexer traces, empty/word laws, exact/over source limit | arbitrary-input tokenization theorem |
| parse | full tree structure, names, quantities, annotations, branch/argument/declaration order | 14 literal trees run in native and Bun, comment transformation, malformed delimiter/indentation cases | full grammar equivalence theorem |
| budget handling | inconclusive failure instead of success | zero-fuel laws; lexer zero/exact/over and parser zero/small runs | general resource-cost bound |
| inspect tree/CLI | complete observable tree or classified failure | both lanes against literal expected strings, invalid CLI-budget check | semantic value interpretation |

The literals in `frontend-cases.json` and the lexer observations in the harness
are explicit expectations; the harness has no lexer, parser or lowering logic.
Six valid no-Base fixtures also run in the pinned reference kernel interpreter
and return `On{}`. Eight negative twins must produce the precise reference
quantity, type, completeness or declaration-order diagnostic, not a parser
failure. They exercise affine reuse, erased live matching, missing arms, forward
live calls, constructor type/arity, shadowing type and constructor inference.

Twenty-four boundary observations (12 cases in two lanes) distinguish lexical
and parser exhaustion, source exact/over limits, unsupported imports/fields/
literals/non-ASCII, missing colon, bad indentation and host argument failure.
Source spans are independently observed by literal lexer traces; tree comparison
intentionally omits spans so prefix comments may preserve the structural tree.
All coverage is finite except the four precisely stated laws above.

## Semantic mutants and hostile review

Every mutant first passes seed syntax/type/quantity checking for the entire
parser CLI. No parser/type failure counts as a semantic kill.

| Mutant | Defining behavior broken | Unchanged rejecting observation |
| --- | --- | --- |
| replace accumulated word spelling with `discarded` | preserve token text | universal `word_source` proof |
| depth zero returns empty parsed sequence | exhaustion never authorizes success | universal `no_parser_budget` proof |
| append parsed head after tail | preserve declaration/argument order | Flag tree literal |
| default parameter quantity becomes reusable | preserve default affine annotation | Flag tree literal |

A constant empty syntax tree is rejected by the full Flag tree observation;
reversing parsed lists and changing binder quantity were implemented and killed.
The boundary laws alone do not establish branch correctness or useful parsing:
the tree observations and order/quantity mutants supply finite evidence for
those behaviors. Missing general preservation/composition proofs remain missing,
not established by the number of passing examples. No optimization or asymptotic
performance claim is made for this first list-based parser.

## Trust and reproduction

Run `python3 tests/subsets/check_frontend.py`. The receipt includes exact
commands, reference diagnostics, generated seed artifact hashes and both lanes.
Seed revision: `574b6d39a235b539eb19a5c532993a0abb3d11ad`. Native compilation
uses the seed C backend/Clang; the seed JavaScript IO path requires Bun 1.3.14
(`bun:ffi`). Future emitted Wasm runs in Node, independently of that bootstrap
IO requirement. Base and the seed checker/backends are trusted dependencies;
this checkpoint does not yet claim a complete native/unsafe closure inventory.

## Source/evidence hashes

- `src/syntax.bend`: `1747ef052e6ee974b2673078db92f9a352f8933a9ad54b573de059b0ae3c8d7b`
- `src/lex.bend`: `1e4668537a254764ecd5b0830511d7b9ee1a21e830d03ae7fea78a1d8578c4b3`
- `src/parse.bend`: `22cc65edc3ba1f50800426e1218c587a89e667a665b8779bdbb5a4ae7895a4ab`
- `src/diagnostic.bend`: `4a53c508ba8d05adfca9bb10a559979e096d5da9095605cf0d34a9c9bb389b73`
- `src/parse-cli.bend`: `7a4feaec7c67c3a8ed7909d46dbef4ca8f5897857b769976f9e2704e67400c90`
- `src/LAWS.bend`: `5db3a525420e9cff3448b0a7219ff71b10a8dc111d6e440007c2a0ae7e8fa76d`
- `src/PROOF.bend`: `c0313e180f55d3941f6bae25a7c4d4362f883495bb54dcb570ef62825eb43a80`
- `tests/subsets/frontend-cases.json`: `34e1c5cb0f68b2d3c5a8c0f35c0cfd5eca22169d5339b4a7369ae31c33c8ff2e`
- `tests/subsets/check_frontend.py`: `c52737859270b500f1558d5df1fb3c3b4e1a96021a465ac8c13b03738de428c1`
- `tests/subsets/receipts/frontend.json`: `a00655b047d442dda28215a15b750d1d0696eda5489b76cd03fe4c2756cb5eeb`

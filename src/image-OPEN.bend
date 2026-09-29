import Base
import ./syntax.bend as S
import ./core.bend as C
import ./image.bend as I
import ./image-plan.bend as P
import ./image-layout.bend as Y

# The round-trip law of the image increment, over every book and fuel, in the form that is true: partial
# correctness. Whenever `encode` answers, decoding its words gives the plan that erasure gave at the same
# fuel. `encode` binds on `erase_tokens`, so an answer implies that erasure succeeded; a refusal by layout
# (too little fuel, a limit of SPEC section 4, a name that is not an identifier) is no answer.
#
# The first statement, `recoded == erase_tokens` at every fuel and book, is false: src/image-LAWS.bend pins
# its counterexamples. This one is required and has no proof: an open claim (D21), recorded in src/SPEC.md
# and tests/compiler-image/LAW_REVIEW.md. It lives in its own file because an open law fails the file that
# states it, and image-LAWS.bend and its PROOF must stay closed. The gate checks that this file reports exactly
# one open claim, and instantiates it as written.
law round_trip:
  for +fuel: Nat
  for +book: C.Book
  for +words: Y.Encoded
  for done: {I.encode(fuel,book) == Done{words} : Result<S.Error,Y.Encoded>}
  {I.recoded(fuel,book) == I.erase_tokens(fuel,book) : Result<S.Error,P.Plan>}

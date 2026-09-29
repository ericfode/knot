import Base
import ./syntax.bend as S
import ./core.bend as C
import ./image.bend as I
import ./image-plan.bend as P

# The round-trip law of the image increment, over every checked book. It is required, and it has no
# proof: an open claim (D21), recorded in src/SPEC.md and tests/compiler-image/LAW_REVIEW.md, with the
# ground instances of image-LAWS.bend as evidence. It lives in its own file because an open law fails the
# file that states it: image-LAWS.bend and its PROOF must stay closed, and the gate checks that this file
# type-checks and reports exactly one open claim, so the statement cannot go stale or be weakened unseen.
law round_trip:
  for +fuel: Nat
  for +book: C.Book
  {I.recoded(fuel,book) == I.erase_tokens(fuel,book) : Result<S.Error,P.Plan>}

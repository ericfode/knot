type Peano is Data:
  Zero{}
  Succ{pred: Peano}
type Flag is Data:
  Off{}
  On{}
type Chain is Type:
  End{}
  Link{head: Flag, tail: Chain}
type Results is Data:
  Results{empty: Peano, three: Peano}
def length(xs: Chain) -> Peano:
  match xs:
    case End{}: Zero{}
    case Link{head,tail}: Succ{length(tail)}
def main() -> Results:
  Results{length(End{}),length(Link{Off{},Link{On{},Link{Off{},End{}}}})}

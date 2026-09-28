type Atom is Data:
  Nine{}
  Eleven{}
type Chain is Data:
  End{}
  Link{value: Atom, next: Chain}
type Tails is Data:
  Tails{left: Chain, right: Chain}
def tails(+chain: Chain) -> Tails:
  match chain:
    case End{}: Tails{End{},End{}}
    case Link{head,tail}: Tails{tail,tail}
def main() -> Tails:
  tails(Link{Nine{},Link{Eleven{},End{}}})

type Flag is Data:
  Off{}
  On{}
type Chain is Type:
  Stop{}
  Next{bit: Flag, tail: Chain}
def last(xs: Chain, acc: Flag) -> Flag:
  match xs:
    case Stop{}: acc
    case Next{bit,tail}:
      unused : Chain = Next{On{},Stop{}}
      last(tail,bit)
def main() -> Flag:
  last(Next{Off{},Next{On{},Stop{}}},Off{})
def empty() -> Flag:
  last(Stop{},Off{})

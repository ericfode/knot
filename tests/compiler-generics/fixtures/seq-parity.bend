# A List-like sequence walked by a structurally recursive generic function.
type Flag is Data:
  Off{}
  On{}

type Parity is Data:
  Even{}
  Odd{}

type Seq<-A: Type> is Type:
  End{}
  Link{head: A, tail: Seq<A>}

def flip(p: Parity) -> Parity:
  match p:
    case Even{}:
      Odd{}
    case Odd{}:
      Even{}

def parity(-A: Type, xs: Seq<A>) -> Parity:
  match xs:
    case End{}:
      Even{}
    case Link{h, t}:
      flip(parity(A, t))

def grow(x: Flag) -> Seq<Flag>:
  match x:
    case Off{}:
      Link{Off{}, End{}}
    case On{}:
      Link{On{}, Link{On{}, End{}}}

def count(x: Flag) -> Parity:
  parity(Flag, grow(x))

def main() -> Parity:
  parity(Flag, Link{On{}, Link{Off{}, Link{On{}, End{}}}})

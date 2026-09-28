# One quantity-polymorphic walk at &2 (Data elements) and &1 (Type elements).
# The compact spelling Seq<&2,Flag> matches the form used across Knot source.
type Flag is Data:
  Off{}
  On{}

type Parity is Data:
  Even{}
  Odd{}

type Box<-A: Type> is Type:
  Box{value: A}

type Seq<a, -A: Kind(a)> is Kind(a):
  End{}
  Link{head: A, tail: Seq<a, A>}

def flip(p: Parity) -> Parity:
  match p:
    case Even{}:
      Odd{}
    case Odd{}:
      Even{}

def parity(a, -A: Kind(a), xs: Seq<a, A>) -> Parity:
  match xs:
    case End{}:
      Even{}
    case Link{h, t}:
      flip(parity(a, A, t))

def flags(x: Flag) -> Seq<&2,Flag>:
  match x:
    case Off{}:
      Link{Off{}, End{}}
    case On{}:
      Link{On{}, Link{Off{}, End{}}}

def boxes(x: Flag) -> Seq<&1,Box<Flag>>:
  match x:
    case Off{}:
      Link{Box{Off{}}, Link{Box{On{}}, End{}}}
    case On{}:
      Link{Box{On{}}, End{}}

def data(x: Flag) -> Parity:
  parity(&2, Flag, flags(x))

def boxed(x: Flag) -> Parity:
  parity(&1, Box<Flag>, boxes(x))

def main() -> Parity:
  parity(&2, Flag, Link{On{}, Link{Off{}, Link{On{}, End{}}}})

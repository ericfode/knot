type Flag is Data:
  Off{}
  On{}

type Seq<a, -A: Kind(a)> is Kind(a):
  End{}
  Link{head: A, tail: Seq<a,A>}

def head(xs: Seq <&2,Flag>) -> Flag:
  match xs:
    case End{}:
      Off{}
    case Link{h,t}:
      h

def second(xs: Seq< &2, Flag>) -> Flag:
  match xs:
    case End{}:
      Off{}
    case Link{h,t}:
      head(t)

def both(x: Flag) -> Flag:
  second(Link{Off{},Link{x,End{}}})

def main() -> Flag:
  both(On{})

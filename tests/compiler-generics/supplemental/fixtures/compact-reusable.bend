# A reusable binder over a compact explicit single-quantity application.
type Flag is Data:
  Off{}
  On{}

type Seq<a, -A: Kind(a)> is Kind(a):
  End{}
  Link{head: A, tail: Seq<a,A>}

def head(ts: Seq<&2,Flag>) -> Flag:
  match ts:
    case End{}:
      Off{}
    case Link{h,t}:
      h

def both(x: Flag, y: Flag) -> Flag:
  match x:
    case Off{}:
      Off{}
    case On{}:
      y

def twice(+ts: Seq<&2,Flag>) -> Flag:
  both(head(ts),head(ts))

def round(x: Flag) -> Flag:
  twice(Link{x,End{}})

def empty() -> Flag:
  twice(End{})

def main() -> Flag:
  round(On{})

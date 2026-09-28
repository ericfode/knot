# The diagnostic.concat shape: Seq<&1,Res<Fault,Flag>> of affine results, folded through bind with a + head capture.
type Flag is Data:
  Off{}
  On{}

type Fault is Data:
  Invalid{}
  Unsupported{}

type Report is Data:
  Rejected{}
  Deferred{}
  Falsy{}
  Truthy{}

type Seq<a, -A: Kind(a)> is Kind(a):
  Stop{}
  Link{head: A, tail: Seq<a, A>}

type Res<a, b, -E: Kind(a), -A: Kind(b)> is Kind(a <&> b):
  Fail{error: E}
  Done{value: A}

def bind(-A: Data, -B: Data, result: Res<Fault,A>, next: A -> Res<Fault,B>) -> Res<Fault,B>:
  match result:
    case Fail{e}: Fail{e}
    case Done{x}: next(x)

def and(x: Flag, y: Flag) -> Flag:
  match x:
    case Off{}: Off{}
    case On{}: y

def concat(parts: Seq<&1,Res<Fault,Flag>>) -> Res<Fault,Flag>:
  match parts:
    case Stop{}: Done{On{}}
    case Link{Fail{e},tail}: Fail{e}
    case Link{Done{+head},tail}:
      bind(Flag,Flag,concat(tail),rest => Done{and(head,rest)})

def part(f: Flag, g: Flag) -> Res<Fault,Flag>:
  match f:
    case Off{}: Fail{Unsupported{}}
    case On{}: Done{g}

def report(r: Res<Fault,Flag>) -> Report:
  match r:
    case Fail{Invalid{}}: Rejected{}
    case Fail{Unsupported{}}: Deferred{}
    case Done{Off{}}: Falsy{}
    case Done{On{}}: Truthy{}

def joined(a: Flag, b: Flag, c: Flag) -> Report:
  report(concat(Link{part(On{},a),Link{part(b,c),Link{Fail{Invalid{}},Stop{}}}}))

def pair(a: Flag, b: Flag) -> Report:
  report(concat(Link{part(On{},a),Link{part(On{},b),Stop{}}}))

def main() -> Report:
  pair(On{},On{})

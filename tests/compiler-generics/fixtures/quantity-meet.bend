# Kind(a <&> b): a pair of two Data kinds is Data, so a +binder may reuse it.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}
  Blue{}

type Pair<a, b, -A: Kind(a), -B: Kind(b)> is Kind(a <&> b):
  Pair{fst: A, snd: B}

def fst(a, b, -A: Kind(a), -B: Kind(b), p: Pair<a, b, A, B>) -> A:
  match p:
    case Pair{x, y}:
      x

def snd(a, b, -A: Kind(a), -B: Kind(b), p: Pair<a, b, A, B>) -> B:
  match p:
    case Pair{x, y}:
      y

def gate(x: Flag, c: Color) -> Color:
  match x:
    case Off{}:
      Red{}
    case On{}:
      c

def both(+p: Pair<&2, &2, Flag, Color>) -> Color:
  gate(fst(&2, &2, Flag, Color, p), snd(&2, &2, Flag, Color, p))

def keep(x: Flag, c: Color) -> Color:
  both(Pair{x, c})

def main() -> Color:
  keep(On{}, Blue{})

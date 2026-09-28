# Negative twin of quantity-meet: Kind(&2 <&> &1) is Type, so +p is rejected.
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

def both(+p: Pair<&2, &1, Color, Flag>) -> Color:
  fst(&2, &1, Color, Flag, p)

def main() -> Color:
  both(Pair{Blue{}, On{}})

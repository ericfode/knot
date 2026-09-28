# Two type parameters: swap permutes them, fst projects and drops the other field.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}
  Blue{}

type Pair<-A: Type, -B: Type> is Type:
  Pair{fst: A, snd: B}

def swap(-A: Type, -B: Type, p: Pair<A, B>) -> Pair<B, A>:
  match p:
    case Pair{a, b}:
      Pair{b, a}

def fst(-A: Type, -B: Type, p: Pair<A, B>) -> A:
  match p:
    case Pair{a, b}:
      a

def second(x: Flag, c: Color) -> Color:
  fst(Color, Flag, swap(Flag, Color, Pair{x, c}))

def first(x: Flag, c: Color) -> Flag:
  fst(Flag, Color, swap(Color, Flag, swap(Flag, Color, Pair{x, c})))

def main() -> Color:
  second(On{}, Green{})

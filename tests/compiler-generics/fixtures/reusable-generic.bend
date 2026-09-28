# A reusable binder at an erased Data type may be copied: +x: A under -A: Data.
type Color is Data:
  Red{}
  Green{}
  Blue{}

type Pair<-A: Type, -B: Type> is Type:
  Pair{fst: A, snd: B}

def dup(-A: Data, +x: A) -> Pair<A, A>:
  Pair{x, x}

def snd(-A: Type, -B: Type, p: Pair<A, B>) -> B:
  match p:
    case Pair{a, b}:
      b

def echo(c: Color) -> Color:
  snd(Color, Color, dup(Color, c))

def main() -> Color:
  echo(Green{})

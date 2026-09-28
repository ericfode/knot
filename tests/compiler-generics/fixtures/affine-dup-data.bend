# Negative twin of reusable-generic: -A: Data alone does not make x reusable.
type Color is Data:
  Red{}
  Green{}
  Blue{}

type Pair<-A: Type, -B: Type> is Type:
  Pair{fst: A, snd: B}

def dup(-A: Data, x: A) -> Pair<A, A>:
  Pair{x, x}

def main() -> Color:
  Green{}

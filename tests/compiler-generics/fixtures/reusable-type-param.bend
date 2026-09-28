# Negative twin of reusable-generic: +x needs a Data type, but -A is only Type.
type Color is Data:
  Red{}
  Green{}
  Blue{}

type Pair<-A: Type, -B: Type> is Type:
  Pair{fst: A, snd: B}

def dup(-A: Type, +x: A) -> Pair<A, A>:
  Pair{x, x}

def main() -> Color:
  Green{}

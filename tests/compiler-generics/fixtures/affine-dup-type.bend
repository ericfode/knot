# Negative twin of reusable-generic: an affine value of an erased Type is copied.
type Color is Data:
  Red{}
  Green{}
  Blue{}

type Pair<-A: Type, -B: Type> is Type:
  Pair{fst: A, snd: B}

def dup(-A: Type, x: A) -> Pair<A, A>:
  Pair{x, x}

def main() -> Color:
  Green{}

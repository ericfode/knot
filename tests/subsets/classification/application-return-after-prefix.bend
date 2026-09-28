type Flag is Data:
  Off{}
  On{}

def main() -> List<:
  Nil{}

type List<-A: Type> is Type:
  Nil{}
  Cons{head: A, tail: List<A>}

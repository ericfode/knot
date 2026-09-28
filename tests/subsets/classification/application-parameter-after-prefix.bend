type Flag is Data:
  Off{}
  On{}

def take(xs: List<) -> Flag:
  On{}

type List<-A: Type> is Type:
  Nil{}
  Cons{head: A, tail: List<A>}

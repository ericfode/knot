type Flag is Data:
  Off{}
  On{}

def main() -> Flag:
  xs: List<Flag> = Nil{}
  On{}

type List<-A: Type> is Type:
  Nil{}
  Cons{head: A, tail: List<A>}

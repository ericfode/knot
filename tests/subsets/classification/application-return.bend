type Flag is Data:
  Off{}
  On{}

def main() -> List<Flag>:
  Nil{}

type List<-A: Type> is Type:
  Nil{}
  Cons{head: A, tail: List<A>}

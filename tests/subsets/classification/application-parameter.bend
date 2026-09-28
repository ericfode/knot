type Flag is Data:
  Off{}
  On{}

def take(xs: List<Flag>) -> Flag:
  On{}

def main() -> Flag:
  take(Nil{})

type List<-A: Type> is Type:
  Nil{}
  Cons{head: A, tail: List<A>}

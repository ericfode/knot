# A parameter type names a type parameter bound after it.
type Flag is Data:
  Off{}
  On{}

type Outcome<-A: Type> is Type:
  Failed{code: Flag}
  Passed{value: A}

def passed(x: A, -A: Type) -> Outcome<A>:
  Passed{x}

def main() -> Flag:
  On{}

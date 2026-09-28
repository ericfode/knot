# Negative twin of alias-type: a +binder behind an alias that unfolds to a Type.
type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{value: A}

def Wrap(A: Type) -> Type:
  Box<A>

def keep(+b: Wrap(Flag)) -> Flag:
  On{}

def main() -> Flag:
  keep(Box{On{}})

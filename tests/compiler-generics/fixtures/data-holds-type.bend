# Negative twin of data-cell: a Data family cannot hold a field of a Type parameter.
type Flag is Data:
  Off{}
  On{}

type Cell<-A: Type> is Data:
  Cell{value: A}

def main() -> Flag:
  On{}

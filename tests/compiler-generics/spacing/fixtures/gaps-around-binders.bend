type Flag is Data:
  Off{}
  On{}

type Seq<a > is Kind(a):
  End{}

type Box< - A: Type> is Type:
  Box{value: A}

def open(- A: Type, b: Box<A>) -> A:
  match b:
    case Box{v}:
      v

def main() -> Flag:
  open(Flag, Box{On{}})

# A parameter named like a type is harmless while no annotation after it reads that name.
type Bit is Data:
  Lo{}
  Hi{}

type Flag is Data:
  Off{}
  On{}

def f(Flag: Bit, b: Bit) -> Bit:
  match b:
    case Lo{}: Hi{}
    case Hi{}: Lo{}

def g(Flag: Bit, +x: Bit) -> Bit:
  y : Bit = x
  y

def main() -> Bit:
  f(g(Lo{}, Lo{}), Hi{})

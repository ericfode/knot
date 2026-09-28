import Base

type Flag is Data:
  Off{}
  On{}

def pred(x: Nat) -> Flag:
  match x:
    case 0n: Off{}
    case 1n+n: On{}

def main() -> Flag:
  pred(2n)

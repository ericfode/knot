import Base

def pred(x: Nat) -> Nat:
  match x:
    case 0n: 0n
    case 1n+n: n

def main() -> Nat:
  pred(3n)

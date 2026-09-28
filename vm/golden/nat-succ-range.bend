import Base

def succ(x: Nat) -> Nat:
  Succ{x}

def main() -> Bool:
  Nat.is_gt(succ(4294967295n),0n)

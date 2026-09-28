import Base

def check(n: Nat) -> Bool:
  match n:
    case 0n: False{}
    case 1n+p: Nat.is_eq(p,2147483648n)

def main() -> Bool:
  check(U32.to_nat(2147483649))

import Base

def drain(n: Nat) -> Bool:
  match n:
    case Zero{}: True{}
    case Succ{p}: drain(p)

def main() -> Bool:
  drain(5000n)

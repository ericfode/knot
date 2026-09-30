import Base

def invert(b: Bool) -> Bool:
  match b:
    case False{}: True{}
    case True{}: False{}

def drain(n: Nat) -> Bool:
  match n:
    case Zero{}: True{}
    case Succ{p}: invert(drain(p))

def main() -> Bool:
  drain(4999n)

import Base

# `U32.add` names Base's intrinsic, so no binder takes it.
type Answer is Type:
  No{}
  Yes{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def f(n: U32) -> U32:
  match n:
    case 0: 1
    case U32.add: U32.add

def main() -> Answer:
  verdict(U32.is_eq(f(9), 9))

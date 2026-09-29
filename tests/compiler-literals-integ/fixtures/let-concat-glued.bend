# The operator may touch its operands: `a++b` is the same concatenation to the seed.
import Base

type Answer is Type:
  No{}
  Yes{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def f(a: String, b: String) -> Answer:
  c : String = a++b
  verdict(String.eq(c, "ab"))

def main() -> Answer:
  f("a", "b")

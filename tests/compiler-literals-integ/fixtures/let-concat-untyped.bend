# The right side of an untyped let may be an operator too: the seed infers the concatenation.
import Base

type Answer is Type:
  No{}
  Yes{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def f(a: String, b: String) -> Answer:
  c = a ++ b
  verdict(String.eq(c, "ab"))

def main() -> Answer:
  f("a", "b")

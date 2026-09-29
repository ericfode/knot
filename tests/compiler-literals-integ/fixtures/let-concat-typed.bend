# The right side of a typed let may be an operator: `a ++ b` concatenates strings, so the seed
# accepts it, and a parser that expected the line to end after `a` would be wrong.
import Base

type Answer is Type:
  No{}
  Yes{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def f(a: String, b: String) -> Answer:
  c : String = a ++ b
  verdict(String.eq(c, "ab"))

def main() -> Answer:
  f("a", "b")

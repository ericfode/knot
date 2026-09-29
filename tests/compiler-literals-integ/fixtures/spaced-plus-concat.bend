# A spaced `+` after an argument may be an operator: `a ++ b` concatenates strings, so the seed
# accepts this call, and a parser that called it a missing comma would be wrong.
import Base

type Answer is Type:
  No{}
  Yes{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def two(a: String, b: String) -> Answer:
  verdict(String.eq(a, b))

def f(a: String, b: String) -> Answer:
  two(a ++ b, "ab")

def main() -> Answer:
  f("a", "b")

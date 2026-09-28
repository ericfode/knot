# Operator sugar over String: a ++ b is String.append(a, b).
import Base

type Answer is Type:
  No{}
  Yes{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def main() -> Answer:
  verdict(String.eq("ab" ++ "cd", "abcd"))

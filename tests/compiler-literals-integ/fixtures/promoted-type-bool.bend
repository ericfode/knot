# Any of Base's types: `+Bool` in a default row.
import Base

type Answer is Type:
  No{}
  Yes{}

def f(v: Nat) -> Answer:
  match v:
    case 0n: No{}
    case +Bool: Yes{}

def main() -> Answer:
  f(3n)

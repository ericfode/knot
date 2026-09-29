# Base's types count too: `+Nat` names the loaded datatype.
import Base

type Answer is Type:
  No{}
  Yes{}

def f(v: Nat) -> Answer:
  match v:
    case 0n: No{}
    case +Nat: Yes{}

def main() -> Answer:
  f(3n)

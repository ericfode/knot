import Base

# The tail of an offset pattern binds one name, which is not a dotted global.
type Answer is Type:
  No{}
  Yes{}

def f(n: Nat) -> Answer:
  match n:
    case 0n: No{}
    case 1n+x.y: Yes{}

def main() -> Answer:
  f(3n)

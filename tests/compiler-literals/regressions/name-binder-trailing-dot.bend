import Base

# A pattern binder is a name, and `x.` is none.
type Answer is Type:
  No{}
  Yes{}

def f(n: U32) -> Answer:
  match n:
    case 0: No{}
    case x.: Yes{}

def main() -> Answer:
  f(9)

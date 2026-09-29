import Base

# A dotted name is a global reference, never a pattern binder, unless a parameter already binds it.
type Answer is Type:
  No{}
  Yes{}

def f(n: U32) -> Answer:
  match n:
    case 0: No{}
    case x.y: Yes{}

def main() -> Answer:
  f(9)

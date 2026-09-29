import Base

# A name is words joined by single dots: `x.` is none, wherever it stands.
type Answer is Type:
  No{}
  Yes{}

def f(x.: U32) -> Answer:
  Yes{}

def main() -> Answer:
  f(5)

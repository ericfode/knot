import Base

# `0n+p` reads as the binder `p`, so it matches any Answer.
type Answer is Type:
  No{}
  Yes{}

def inspect(a: Answer) -> Answer:
  match a:
    case 0n+p: p

def main() -> Answer:
  inspect(Yes{})

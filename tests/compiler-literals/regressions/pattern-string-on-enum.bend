import Base

# A String literal pattern names no constructor of Answer.
type Answer is Type:
  No{}
  Yes{}

def inspect(a: Answer) -> Answer:
  match a:
    case "a": No{}
    case _: Yes{}

def main() -> Answer:
  inspect(Yes{})

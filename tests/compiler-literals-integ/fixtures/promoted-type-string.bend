# The String type of Base, promoted in a default row.
import Base

type Answer is Type:
  No{}
  Yes{}

def f(v: String) -> Answer:
  match v:
    case "a": No{}
    case +String: Yes{}

def main() -> Answer:
  f("b")

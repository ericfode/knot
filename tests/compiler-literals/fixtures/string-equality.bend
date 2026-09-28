# String.eq over literals, including the empty string and prefixes.
import Base

type Answer is Type:
  No{}
  Yes{}

type Text is Type:
  Blank{}
  A{}
  AB{}
  B{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def text(t: Text) -> String:
  match t:
    case Blank{}: ""
    case A{}: "a"
    case AB{}: "ab"
    case B{}: "b"

def equal(x: Text, y: Text) -> Answer:
  verdict(String.eq(text(x), text(y)))

def main() -> Answer:
  equal(AB{}, AB{})

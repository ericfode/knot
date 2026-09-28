# String.append concatenates; the empty string is its identity on both sides.
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

def spells_ab(x: Text, y: Text) -> Answer:
  verdict(String.eq(String.append(text(x), text(y)), "ab"))

def main() -> Answer:
  spells_ab(A{}, B{})

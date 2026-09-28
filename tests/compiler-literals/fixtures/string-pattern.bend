# String literal patterns beside constructor patterns with a Char literal head.
import Base

type Shape is Type:
  Exact{}
  Prefixed{}
  Other{}

type Text is Type:
  Blank{}
  AB{}
  AX{}
  B{}

def text(t: Text) -> String:
  match t:
    case Blank{}: ""
    case AB{}: "ab"
    case AX{}: "ax"
    case B{}: "b"

def kind(s: String) -> Shape:
  match s:
    case "ab": Exact{}
    case SCon{'a', t}: Prefixed{}
    case _: Other{}

def classify(t: Text) -> Shape:
  kind(text(t))

def main() -> Shape:
  classify(AX{})

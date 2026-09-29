import Base

# An escape before `{` is still an escape; only `\u{` and `\U{` open a code point.
type Answer is Type:
  No{}
  Yes{}

type Escape is Data:
  Newline{}
  Backslash{}
  Quote{}
  Apostrophe{}
  Tab{}
  Return{}
  Nul{}
  Closing{}
  Plain{}
  Point{}
  UpperPoint{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def spelled(e: Escape) -> String:
  match e:
    case Newline{}: "\n{"
    case Backslash{}: "\\{"
    case Quote{}: "\"{"
    case Apostrophe{}: "\'{"
    case Tab{}: "x\t{y"
    case Return{}: "\r{"
    case Nul{}: "\0{"
    case Closing{}: "\n}"
    case Plain{}: "ab{"
    case Point{}: "\u{41}{"
    case UpperPoint{}: "\U{41}{"

def split(e: Escape) -> String:
  match e:
    case Newline{}: String.append("\n", "{")
    case Backslash{}: String.append("\\", "{")
    case Quote{}: String.append("\"", "{")
    case Apostrophe{}: String.append("\'", "{")
    case Tab{}: String.append("x\t", "{y")
    case Return{}: String.append("\r", "{")
    case Nul{}: String.append("\0", "{")
    case Closing{}: String.append("\n", "}")
    case Plain{}: String.append("ab", "{")
    case Point{}: String.append("A", "{")
    case UpperPoint{}: String.append("A", "{")

def pair(e: Escape) -> Answer:
  answer(Nat.is_eq(String.length(spelled(e)), 2n))

def decoded(+e: Escape) -> Answer:
  answer(String.eq(spelled(e), split(e)))

def main() -> Answer:
  pair(Tab{})

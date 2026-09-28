import Base

type Text is Data:
  HexNumber{}
  HexMark{}
  Nought{}
  Blank{}
  UpperHex{}
  Swapped{}
  Dot{}

type Prefix is Data:
  Mark{}
  Nothing{}
  Longer{}

type Verdict is Data:
  No{}
  Yes{}

def text(t: Text) -> String:
  match t:
    case HexNumber{}: "0x1f"
    case HexMark{}: "0x"
    case Nought{}: "0"
    case Blank{}: ""
    case UpperHex{}: "0X1f"
    case Swapped{}: "x0"
    case Dot{}: "."

def prefix(p: Prefix) -> String:
  match p:
    case Mark{}: "0x"
    case Nothing{}: ""
    case Longer{}: "0x1f0"

def verdict(b: Bool) -> Verdict:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def prefixed(t: Text, p: Prefix) -> Verdict:
  verdict(String.starts_with(text(t), prefix(p)))

# parse.run: a dotted name or a 0x hash path marks a qualified reference.
def qualified(t: Text) -> Verdict:
  +s = text(t)
  verdict(Bool.or(String.eq(s, "."), String.starts_with(s, "0x")))

def main() -> Verdict:
  prefixed(HexNumber{}, Mark{})

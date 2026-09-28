# A Nat fuel column beside SNil/SCon columns, in src/lex.bend's `scan` shape:
# `case _ SNil{}` first, then `case 0n SCon{..}` and `case 1n+n SCon{..}`.
import Base

type Level is Type:
  Starved{}
  Even{}
  Odd{}

type Budget is Type:
  B0{}
  B2{}
  B3{}

type Text is Type:
  Blank{}
  Two{}
  Three{}

type Parity is Data:
  Evens{}
  Odds{}

def flip(p: Parity) -> Parity:
  match p:
    case Evens{}: Odds{}
    case Odds{}: Evens{}

def done(p: Parity) -> Level:
  match p:
    case Evens{}: Even{}
    case Odds{}: Odd{}

def scan(fuel: Nat, input: String, parity: Parity) -> Level:
  match fuel input:
    case _ SNil{}: done(parity)
    case 0n SCon{c,tail}: Starved{}
    case 1n+n SCon{c,tail}: scan(n,tail,flip(parity))

def budget(b: Budget) -> Nat:
  match b:
    case B0{}: 0n
    case B2{}: 2n
    case B3{}: 3n

def text(t: Text) -> String:
  match t:
    case Blank{}: ""
    case Two{}: "ab"
    case Three{}: "abc"

def probe(b: Budget, t: Text) -> Level:
  scan(budget(b),text(t),Evens{})

def main() -> Level:
  probe(B3{},Three{})

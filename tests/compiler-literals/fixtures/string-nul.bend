# NUL is an ordinary Char inside a String: it neither ends nor pads it.
import Base

type Answer is Type:
  No{}
  Yes{}

type Case is Type:
  Length{}
  Trailing{}
  Single{}
  Interior{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def check(c: Case) -> Answer:
  match c:
    case Length{}: verdict(Nat.is_eq(String.length("a\0b"), 3n))
    case Trailing{}: verdict(String.eq("a", "a\0"))
    case Single{}: verdict(String.eq("\0", SCon{Chr{0}, SNil{}}))
    case Interior{}: verdict(String.eq("a\0b", "a\0c"))

def main() -> Answer:
  check(Length{})

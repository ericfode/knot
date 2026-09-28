# Inside a String, # is not a comment, ' needs no escape, and a raw newline is kept.
import Base

type Answer is Type:
  No{}
  Yes{}

type Trap is Type:
  Hash{}
  Apostrophe{}
  Newline{}
  Length{}
  Truncated{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def check(t: Trap) -> Answer:
  match t:
    case Hash{}: verdict(String.eq("a#b", SCon{'a', SCon{'#', SCon{'b', SNil{}}}}))
    case Apostrophe{}: verdict(String.eq("'", SCon{'\'', SNil{}}))
    case Newline{}: verdict(String.eq("a
b", "a\nb"))
    case Length{}: verdict(Nat.is_eq(String.length("# x"), 3n))
    case Truncated{}: verdict(Nat.is_eq(String.length("a#b"), 1n))

def main() -> Answer:
  check(Hash{})

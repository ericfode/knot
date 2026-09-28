# String escapes: each denotes one Char; "\\n" is two chars, not a newline.
import Base

type Answer is Type:
  No{}
  Yes{}

type Case is Type:
  Chain{}
  Length{}
  Spelled{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def check(c: Case) -> Answer:
  match c:
    case Chain{}:
      verdict(String.eq("\n\t\r\\\"\'", SCon{Chr{10}, SCon{Chr{9}, SCon{Chr{13}, SCon{Chr{92}, SCon{Chr{34}, SCon{Chr{39}, SNil{}}}}}}}))
    case Length{}:
      verdict(Nat.is_eq(String.length("\n\t\r\\\"\'"), 6n))
    case Spelled{}:
      verdict(String.eq("\\n", "\n"))

def main() -> Answer:
  check(Chain{})

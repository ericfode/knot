# A literal and its spelled-out Base constructor tree are the same value.
import Base

type Answer is Type:
  No{}
  Yes{}

type View is Type:
  NatTwo{}
  NatPrefix{}
  CharA{}
  StringHi{}
  StringEmpty{}
  NatOne{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def same(v: View) -> Answer:
  match v:
    case NatTwo{}: verdict(Nat.is_eq(Succ{Succ{Zero{}}}, 2n))
    case NatPrefix{}: verdict(Nat.is_eq(1n+Succ{Zero{}}, 2n))
    case CharA{}: verdict(Char.is_eq(Chr{65}, 'A'))
    case StringHi{}: verdict(String.eq(SCon{'h', SCon{'i', SNil{}}}, "hi"))
    case StringEmpty{}: verdict(String.eq(SNil{}, ""))
    case NatOne{}: verdict(Nat.is_eq(Succ{Zero{}}, 2n))

def main() -> Answer:
  same(NatTwo{})

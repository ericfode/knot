import Base

# A promoted binder copies its value even when other rows split its column.
type Answer is Type:
  No{}
  Yes{}

type Size is Type:
  Empty{}
  One{}
  Two{}
  Three{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def size(s: Size) -> Nat:
  match s:
    case Empty{}: 0n
    case One{}: 1n
    case Two{}: 2n
    case Three{}: 3n

def text(s: Size) -> String:
  match s:
    case Empty{}: ""
    case One{}: "ab"
    case Two{}: "bc"
    case Three{}: "abc"

def after_literals(n: Nat) -> Answer:
  match n:
    case 0n: No{}
    case 1n: No{}
    case 1n+ +p: answer(Nat.is_eq(Nat.add(p, p), 2n))

def after_offset(n: Nat) -> Answer:
  match n:
    case 0n: No{}
    case 2n+q: No{}
    case 1n+ +p: answer(Nat.is_eq(Nat.add(p, p), 0n))

def default(n: Nat) -> Answer:
  match n:
    case 0n: No{}
    case +x: answer(Nat.is_eq(Nat.add(x, x), 4n))

def first(n: Nat) -> Answer:
  match n:
    case +x: answer(Nat.is_eq(Nat.add(x, x), 4n))
    case 0n: No{}

def unlettered(n: Nat) -> Answer:
  match n:
    case Zero{}: No{}
    case +x: answer(Nat.is_eq(Nat.add(x, x), Succ{Succ{Succ{Succ{Zero{}}}}}))

def doubled(s: String) -> Answer:
  match s:
    case "": No{}
    case +x: answer(String.eq(String.append(x, x), "abab"))

def tail(s: String) -> Answer:
  match s:
    case "ab": No{}
    case SCon{c, +t}: answer(String.eq(String.append(t, t), "cc"))
    case _: No{}

def nat_after_literals(s: Size) -> Answer:
  after_literals(size(s))

def nat_after_offset(s: Size) -> Answer:
  after_offset(size(s))

def nat_default(s: Size) -> Answer:
  default(size(s))

def nat_first(s: Size) -> Answer:
  first(size(s))

def nat_unlettered(s: Size) -> Answer:
  unlettered(size(s))

def string_default(s: Size) -> Answer:
  doubled(text(s))

def string_tail(s: Size) -> Answer:
  tail(text(s))

def main() -> Answer:
  nat_after_literals(Two{})

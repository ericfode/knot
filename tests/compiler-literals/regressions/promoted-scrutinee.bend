import Base

# A promoted catch-all promotes its scrutinee in that arm, so both may be used twice.
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

def word(s: Size) -> U32:
  match s:
    case Empty{}: 0
    case One{}: 1
    case Two{}: 2
    case Three{}: 3

def text(s: Size) -> String:
  match s:
    case Empty{}: ""
    case One{}: "ab"
    case Two{}: "bc"
    case Three{}: "abc"

def alone(n: Nat) -> Answer:
  match n:
    case +x: answer(Nat.is_eq(Nat.add(n, n), 4n))

def after_literal(n: Nat) -> Answer:
  match n:
    case 0n: No{}
    case +x: answer(Nat.is_eq(Nat.add(n, n), 4n))

def after_constructor(n: Nat) -> Answer:
  match n:
    case Zero{}: No{}
    case +x: answer(Nat.is_eq(Nat.add(n, n), 4n))

def beside(n: Nat) -> Answer:
  match n:
    case 0n: No{}
    case +x: answer(Nat.is_eq(Nat.add(x, n), 4n))

def doubled(s: String) -> Answer:
  match s:
    case "": No{}
    case +x: answer(String.eq(String.append(s, s), "abab"))

def tail(s: String) -> Answer:
  match s:
    case "ab": No{}
    case SCon{c, +t}: answer(String.eq(String.append(t, s), "cbc"))
    case _: No{}

def twice(w: U32) -> Answer:
  match w:
    case 0: No{}
    case +x: answer(U32.is_eq(U32.add(w, w), 4))

def nat_alone(s: Size) -> Answer:
  alone(size(s))

def nat_after_literal(s: Size) -> Answer:
  after_literal(size(s))

def nat_after_constructor(s: Size) -> Answer:
  after_constructor(size(s))

def nat_beside(s: Size) -> Answer:
  beside(size(s))

def string_doubled(s: Size) -> Answer:
  doubled(text(s))

def string_tail(s: Size) -> Answer:
  tail(text(s))

def u32_twice(s: Size) -> Answer:
  twice(word(s))

def main() -> Answer:
  nat_after_literal(Two{})

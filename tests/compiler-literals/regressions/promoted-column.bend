import Base

# One `+` row promotes its column, and the column's fields, in every row of the match.
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

def letter(s: Size) -> Char:
  match s:
    case Empty{}: 'a'
    case One{}: 'b'
    case Two{}: 'c'
    case Three{}: 'd'

def text(s: Size) -> String:
  match s:
    case Empty{}: ""
    case One{}: "ab"
    case Two{}: "bc"
    case Three{}: "abc"

def offset(v: Nat) -> Answer:
  match v:
    case 0n: No{}
    case 1n+p: answer(Nat.is_eq(Nat.add(p, p), 4n))
    case +x: No{}

def successor(v: Nat) -> Answer:
  match v:
    case Zero{}: No{}
    case Succ{p}: answer(Nat.is_eq(Nat.add(p, p), 4n))
    case +x: No{}

def deep(v: Nat) -> Answer:
  match v:
    case 0n: No{}
    case 1n: No{}
    case 2n+p: answer(Nat.is_eq(Nat.add(v, v), 4n))
    case +x: No{}

def inner(v: Nat) -> Answer:
  match v:
    case 0n: No{}
    case 1n: No{}
    case 2n+p: answer(Nat.is_eq(Nat.add(v, v), 4n))
    case 1n+ +q: No{}

def unreached(v: Nat) -> Answer:
  match v:
    case x: answer(Nat.is_eq(Nat.add(v, v), 4n))
    case +y: No{}

def tail(v: String) -> Answer:
  match v:
    case "": No{}
    case SCon{c, t}: answer(String.eq(String.append(t, t), "cc"))
    case +x: No{}

def whole(v: String) -> Answer:
  match v:
    case "ab": No{}
    case SCon{c, t}: answer(String.eq(String.append(v, v), "bcbc"))
    case +x: No{}

def twice(v: U32) -> Answer:
  match v:
    case 0: No{}
    case x: answer(U32.is_eq(U32.add(v, v), 4))
    case +y: No{}

def same(v: Char) -> Answer:
  match v:
    case 'a': No{}
    case x: answer(Bool.and(Char.is_eq(v, 'c'), Char.is_eq(v, 'c')))
    case +y: No{}

def nat_offset(s: Size) -> Answer:
  offset(size(s))

def nat_successor(s: Size) -> Answer:
  successor(size(s))

def nat_deep(s: Size) -> Answer:
  deep(size(s))

def nat_inner(s: Size) -> Answer:
  inner(size(s))

def nat_unreached(s: Size) -> Answer:
  unreached(size(s))

def string_tail(s: Size) -> Answer:
  tail(text(s))

def string_whole(s: Size) -> Answer:
  whole(text(s))

def u32_twice(s: Size) -> Answer:
  twice(word(s))

def char_same(s: Size) -> Answer:
  same(letter(s))

def main() -> Answer:
  nat_deep(Two{})

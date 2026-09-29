import Base

# An annotation supplies the type each literal and Nat offset checks against.
type Answer is Type:
  No{}
  Yes{}

type Probe is Type:
  Low{}
  High{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def count(p: Probe) -> Nat:
  match p:
    case Low{}: 1n
    case High{}: 2n

def word(p: Probe) -> Answer:
  n : U32 = 3
  answer(U32.is_eq(n, U32.add(U32.from_nat(count(p)), 2)))

def letter(p: Probe) -> Answer:
  +c : Char = 'a'
  answer(Char.is_eq(c, Char.from_u32(U32.add(Char.to_u32(c), U32.sub(U32.from_nat(count(p)), 1)))))

def number(p: Probe) -> Answer:
  n : Nat = 2n+count(p)
  answer(Nat.is_eq(n, 3n))

def text(p: Probe) -> Answer:
  s : String = "ab"
  answer(Nat.is_eq(String.length(s), count(p)))

def main() -> Answer:
  word(Low{})

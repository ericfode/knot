import Base

# An offset needs `+` adjacent to its literal; spaces after `+` are free.
type Answer is Type:
  No{}
  Yes{}

type Size is Type:
  Empty{}
  Three{}

def size(s: Size) -> Nat:
  match s:
    case Empty{}: 0n
    case Three{}: 3n

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def spaced(n: Nat) -> Answer:
  match n:
    case 0n: No{}
    case 1n+ p: Yes{}

def promoted(n: Nat) -> Answer:
  match n:
    case 0n: No{}
    case 1n+ +p: Yes{}

def joined(n: Nat) -> Answer:
  match n:
    case 0n: No{}
    case 1n++p: Yes{}

def after_space(s: Size) -> Answer:
  spaced(size(s))

def after_promotion(s: Size) -> Answer:
  promoted(size(s))

def after_join(s: Size) -> Answer:
  joined(size(s))

def sum(s: Size) -> Answer:
  answer(Nat.is_eq(3n+ size(s), 6n))

def main() -> Answer:
  after_space(Three{})

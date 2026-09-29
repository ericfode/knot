import Base

# The seed registers constructors in source order, so a pattern binder may take the name of a
# constructor declared after its function: a default, promoted, field or offset binder.
type Answer is Type:
  No{}
  Yes{}

type Probe is Data:
  Low{}
  High{}

type Box is Type:
  Box{v: U32}

def word(p: Probe) -> U32:
  match p:
    case Low{}: 0
    case High{}: 2

def count(p: Probe) -> Nat:
  match p:
    case Low{}: 0n
    case High{}: 2n

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def both(a: Answer, b: Answer) -> Answer:
  match a:
    case No{}: No{}
    case Yes{}: b

def by_default(n: U32) -> Answer:
  match n:
    case 0: No{}
    case Late: answer(U32.is_eq(Late, 2))

def by_promotion(n: U32) -> Answer:
  match n:
    case 0: No{}
    case +Late: answer(U32.is_eq(Late, Late))

def by_field(b: Box) -> Answer:
  match b:
    case Box{Late}: answer(U32.is_eq(Late, 2))

def by_offset(n: Nat) -> Answer:
  match n:
    case 0n: No{}
    case 1n+Late: answer(Nat.is_eq(Late, 1n))

type Later is Type:
  Late{}

def binders(+p: Probe) -> Answer:
  both(by_default(word(p)), both(by_promotion(word(p)), both(by_field(Box{word(p)}), by_offset(count(p)))))

def main() -> Answer:
  binders(High{})

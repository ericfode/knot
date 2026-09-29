import Base

# A dotted name is a binder only where a parameter already binds it, and a constructor is
# no binder once declared, in source order: a later constructor, a parameter, a function and a
# type may all name a binder.
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

def boxed(p: Probe) -> Box:
  Box{word(p)}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def both(a: Answer, b: Answer) -> Answer:
  match a:
    case No{}: No{}
    case Yes{}: b

def by_default(x.y: U32) -> Answer:
  match x.y:
    case 0: No{}
    case x.y: Yes{}

def by_promotion(x.y: U32) -> Answer:
  match x.y:
    case 0: No{}
    case +x.y: Yes{}

def by_offset(x.y: Nat) -> Answer:
  match x.y:
    case 0n: No{}
    case 1n+x.y: Yes{}

def by_field(x.y: Box) -> Answer:
  match x.y:
    case Box{x.y}: answer(U32.is_eq(x.y, 2))

def by_let(x.y: U32) -> Answer:
  x.y : U32 = 3
  answer(U32.is_eq(x.y, 3))

def by_promoted_let(x.y: U32) -> Answer:
  +x.y : U32 = 3
  answer(U32.is_eq(x.y, 3))

def by_plain_let(x.y: U32) -> Answer:
  x.y = word(High{})
  answer(U32.is_eq(x.y, 2))

def late_let(p: Probe) -> Answer:
  Late : U32 = word(p)
  Yes{}

def parameter(True: U32) -> Answer:
  Yes{}

def function_let(p: Probe) -> Answer:
  word : U32 = 3
  answer(U32.is_eq(word, 3))

def type_binder(x: U32) -> Answer:
  match x:
    case 0: No{}
    case Answer: Yes{}

type Later is Type:
  Late{}

def dotted(+p: Probe) -> Answer:
  both(by_default(word(p)), both(by_promotion(word(p)), both(by_offset(count(p)), by_field(boxed(p)))))

def lets(+p: Probe) -> Answer:
  both(by_let(word(p)), both(by_promoted_let(word(p)), both(by_plain_let(word(p)), both(late_let(p), both(parameter(word(p)), both(function_let(p), type_binder(word(p))))))))

def main() -> Answer:
  dotted(High{})

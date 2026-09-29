import Base

# `0n+t` reads as t itself: zero successors around t, so t keeps its own type.
type Answer is Type:
  No{}
  Yes{}

type Probe is Type:
  Three{}
  Four{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def count(p: Probe) -> Nat:
  match p:
    case Three{}: 3n
    case Four{}: 4n

def word(p: Probe) -> U32:
  match p:
    case Three{}: 3
    case Four{}: 4

def spelled(p: Probe) -> String:
  match p:
    case Three{}: "a"
    case Four{}: ""

def counted(n: Nat) -> Answer:
  match n:
    case 3n: No{}
    case 0n+m: answer(Nat.is_eq(m, 4n))

def worded(x: U32) -> Answer:
  match x:
    case 3: No{}
    case 0n+w: answer(U32.is_eq(w, 4))

def texted(s: String) -> Answer:
  match s:
    case "a": No{}
    case 0n+t: answer(String.is_empty(t))

def scrutinized(x: U32) -> Answer:
  match 0n+x:
    case 4: Yes{}
    case _: No{}

def inferred(p: Probe) -> Answer:
  n = 0n+count(p)
  answer(Nat.is_eq(n, 4n))

def checked(p: Probe) -> Answer:
  answer(U32.is_eq(0n+word(p), 4))

def scrutinee(p: Probe) -> Answer:
  scrutinized(word(p))

def nat_binder(p: Probe) -> Answer:
  counted(count(p))

def u32_binder(p: Probe) -> Answer:
  worded(word(p))

def string_binder(p: Probe) -> Answer:
  texted(spelled(p))

def main() -> Answer:
  checked(Four{})

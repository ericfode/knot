import Base

# Primitive String traversals at 40000 Chars, inside the 1048576 bound.
type Answer is Type:
  No{}
  Yes{}

type Size is Type:
  Short{}
  Long{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def size(s: Size) -> Nat:
  match s:
    case Short{}: 39999n
    case Long{}: 40000n

def xs(n: Nat) -> String:
  match n:
    case 0n: ""
    case 1n+p: SCon{'x', xs(p)}

def length(s: Size) -> Answer:
  answer(Nat.is_eq(String.length(xs(size(s))), 40000n))

def append_left(s: Size) -> Answer:
  answer(Nat.is_eq(String.length(String.append(xs(size(s)), "y")), 40001n))

def append_right(s: Size) -> Answer:
  answer(Nat.is_eq(String.length(String.append("y", xs(size(s)))), 40001n))

def reflexive(+t: String) -> Answer:
  answer(String.eq(t, String.append(t, "")))

def equal(s: Size) -> Answer:
  reflexive(xs(size(s)))

def main() -> Answer:
  length(Long{})

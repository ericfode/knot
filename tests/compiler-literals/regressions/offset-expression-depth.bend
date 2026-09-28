import Base

# `kn+t` is k successors around a shared t, so recursion through an expression
# offset allocates in proportion to its depth, as in the seed.
type Answer is Type:
  No{}
  Yes{}

def answer(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def up(n: Nat) -> Nat:
  match n:
    case 0n: 0n
    case 1n+p: 1n+up(p)

def triple(n: Nat) -> Nat:
  match n:
    case 0n: 0n
    case 1n+p: 3n+triple(p)

def kept(n: Nat) -> Nat:
  match n:
    case 0n: 0n
    case 1n+p: Succ{0n+kept(p)}

def successor() -> Answer:
  answer(Nat.is_eq(up(4000n), 4000n))

def successor_short() -> Answer:
  answer(Nat.is_eq(up(4000n), 3999n))

def doubled() -> Answer:
  answer(Nat.is_eq(Nat.double(3000n), 6000n))

def tripled() -> Answer:
  answer(Nat.is_eq(triple(3000n), 9000n))

def zero() -> Answer:
  answer(Nat.is_eq(kept(4000n), 4000n))

def main() -> Answer:
  successor()

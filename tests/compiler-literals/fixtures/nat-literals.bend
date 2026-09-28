# Nat literals, including past 256n, agree with U32.to_nat; n+m literals fold.
import Base

type Answer is Type:
  No{}
  Yes{}

type Size is Data:
  S0{}
  S5{}
  S256{}
  S257{}
  S65536{}

type Fold is Type:
  Small{}
  Wide{}
  Chain{}
  Miss{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def nat(s: Size) -> Nat:
  match s:
    case S0{}: 0n
    case S5{}: 5n
    case S256{}: 256n
    case S257{}: 257n
    case S65536{}: 65536n

def word(s: Size) -> U32:
  match s:
    case S0{}: 0
    case S5{}: 5
    case S256{}: 256
    case S257{}: 257
    case S65536{}: 65536

def agrees(+s: Size) -> Answer:
  verdict(Nat.is_eq(nat(s), U32.to_nat(word(s))))

def is_zero(s: Size) -> Answer:
  verdict(Nat.is_eq(nat(s), 0n))

def folded(f: Fold) -> Answer:
  match f:
    case Small{}: verdict(Nat.is_eq(3n+4n, 7n))
    case Wide{}: verdict(Nat.is_eq(300n+1n, 301n))
    case Chain{}: verdict(Nat.is_eq(1n+2n+3n, 6n))
    case Miss{}: verdict(Nat.is_eq(2n+2n, 5n))

def main() -> Answer:
  agrees(S257{})

# Structural recursion on Nat through the 0n / 1n+p patterns.
import Base

type Parity is Type:
  Even{}
  Odd{}

type Size is Type:
  S0{}
  S1{}
  S5{}
  S256{}
  S257{}

def flip(p: Parity) -> Parity:
  match p:
    case Even{}: Odd{}
    case Odd{}: Even{}

def parity(n: Nat) -> Parity:
  match n:
    case 0n: Even{}
    case 1n+p: flip(parity(p))

def nat(s: Size) -> Nat:
  match s:
    case S0{}: 0n
    case S1{}: 1n
    case S5{}: 5n
    case S256{}: 256n
    case S257{}: 257n

def parity_of(s: Size) -> Parity:
  parity(nat(s))

def deep() -> Parity:
  parity(65536n)

def main() -> Parity:
  parity_of(S5{})

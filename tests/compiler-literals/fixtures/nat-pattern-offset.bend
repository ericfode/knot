# Nat patterns with a literal offset: 2n+p recursion and the 256n+p ceiling.
import Base

type Answer is Type:
  No{}
  Yes{}

type Parity is Type:
  Even{}
  Odd{}

type Size is Type:
  S0{}
  S1{}
  S7{}
  S255{}
  S256{}
  S300{}

def nat(s: Size) -> Nat:
  match s:
    case S0{}: 0n
    case S1{}: 1n
    case S7{}: 7n
    case S255{}: 255n
    case S256{}: 256n
    case S300{}: 300n

def halve(n: Nat) -> Parity:
  match n:
    case 0n: Even{}
    case 1n: Odd{}
    case 2n+p: halve(p)

def past(n: Nat) -> Answer:
  match n:
    case 256n+p: Yes{}
    case _: No{}

def parity_of(s: Size) -> Parity:
  halve(nat(s))

def at_least_256(s: Size) -> Answer:
  past(nat(s))

def main() -> Parity:
  parity_of(S7{})

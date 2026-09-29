# A Nat result displays as the seed's literal, decimal digits and n.
import Base

type Sample is Type:
  Nothing{}
  Three{}
  Sum{}
  Saturated{}
  FromWord{}
  Largest{}

def sample(s: Sample) -> Nat:
  match s:
    case Nothing{}: 0n
    case Three{}: 3n
    case Sum{}: Nat.add(2n, 3n)
    case Saturated{}: Nat.sub(2n, 5n)
    case FromWord{}: U32.to_nat(300)
    case Largest{}: 256n

def main() -> Nat:
  sample(Three{})

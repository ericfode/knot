# Base conversions between U32, Nat, Char and their String renderings.
import Base

type Answer is Type:
  No{}
  Yes{}

type Conversion is Type:
  ToNat{}
  FromNat{}
  CharCode{}
  CodeChar{}
  ShowMax{}
  ShowZero{}
  ShowNat{}
  NoPadding{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def holds(c: Conversion) -> Answer:
  match c:
    case ToNat{}: verdict(Nat.is_eq(U32.to_nat(7), 7n))
    case FromNat{}: verdict(U32.is_eq(U32.from_nat(300n), 300))
    case CharCode{}: verdict(U32.is_eq(Char.to_u32('A'), 65))
    case CodeChar{}: verdict(Char.is_eq(Char.from_u32(97), 'a'))
    case ShowMax{}: verdict(String.eq(U32.show(4294967295), "4294967295"))
    case ShowZero{}: verdict(String.eq(U32.show(0), "0"))
    case ShowNat{}: verdict(String.eq(Nat.show(1000n), "1000"))
    case NoPadding{}: verdict(String.eq(U32.show(10), "010"))

def main() -> Answer:
  holds(ShowMax{})

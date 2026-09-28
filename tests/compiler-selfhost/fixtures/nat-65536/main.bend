# The Nat literal 65536n (a catalog-scale bound in src/) agrees with
# U32.to_nat at and around it.
import Base

type Answer is Type:
  No{}
  Yes{}

type Size is Type:
  Below{}
  At{}
  Above{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def word(s: Size) -> U32:
  match s:
    case Below{}: 65535
    case At{}: 65536
    case Above{}: 65537

def agrees(s: Size) -> Answer:
  verdict(Nat.is_eq(65536n,U32.to_nat(word(s))))

def main() -> Answer:
  agrees(At{})

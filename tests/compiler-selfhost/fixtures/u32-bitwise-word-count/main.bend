# Twin of u32-bitwise-edges: a U32 literal stands where shln's Nat count is expected.
import Base

type Answer is Type:
  No{}
  Yes{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def main() -> Answer:
  verdict(U32.is_eq(U32.shln(1,31),2147483648))

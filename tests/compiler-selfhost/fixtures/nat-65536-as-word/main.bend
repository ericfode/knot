# Twin of nat-65536: the Nat literal stands where a U32 is expected.
import Base

type Answer is Type:
  No{}
  Yes{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def main() -> Answer:
  verdict(U32.is_eq(65536n,65536))

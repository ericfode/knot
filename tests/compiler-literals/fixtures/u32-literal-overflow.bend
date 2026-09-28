# Negative: 4294967296 does not fit a U32 literal (control: u32-literals).
import Base

type Answer is Type:
  No{}
  Yes{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def main() -> Answer:
  verdict(U32.is_eq(4294967296, 0))

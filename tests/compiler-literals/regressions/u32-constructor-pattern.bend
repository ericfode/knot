import Base

# Base spells U32 as U32{data: Word(32n)}; Knot's U32 is unboxed bits.
type Answer is Type:
  No{}
  Yes{}

def word(x: U32) -> Answer:
  match x:
    case U32{w}: Yes{}

def main() -> Answer:
  word(3)

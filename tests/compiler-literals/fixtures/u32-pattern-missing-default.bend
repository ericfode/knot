# Negative: a U32 match without a default arm is not exhaustive.
import Base

type Answer is Type:
  No{}
  Yes{}

def five(x: U32) -> Answer:
  match x:
    case 0: No{}
    case 5: Yes{}

def main() -> Answer:
  five(5)

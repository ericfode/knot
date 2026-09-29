# Whitespace separates call arguments to the seed, literals too: `two(3 4)` passes two arguments.
import Base

type Answer is Type:
  No{}
  Yes{}

def two(a: U32, b: U32) -> Answer:
  Yes{}

def main() -> Answer:
  two(3 4)

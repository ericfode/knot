# A list literal where a Flag is expected.
import Base

type Flag is Data:
  Off{}
  On{}

def run(f: Flag) -> Flag:
  [f]

def main() -> Flag:
  run(On{})

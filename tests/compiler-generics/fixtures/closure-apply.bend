# A generic higher-order apply: seed-valid, but function values are closures.
type Flag is Data:
  Off{}
  On{}

def apply(-A: Type, -B: Type, f: A -> B, x: A) -> B:
  f(x)

def invert(x: Flag) -> Flag:
  match x:
    case Off{}:
      On{}
    case On{}:
      Off{}

def run(x: Flag) -> Flag:
  apply(Flag, Flag, invert, x)

def main() -> Flag:
  run(Off{})

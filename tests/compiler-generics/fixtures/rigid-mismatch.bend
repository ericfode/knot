# Two distinct type parameters are rigid: a value of A is not a value of B.
type Flag is Data:
  Off{}
  On{}

def coerce(-A: Type, -B: Type, x: A) -> B:
  x

def main() -> Flag:
  On{}

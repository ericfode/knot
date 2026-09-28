# Negative twin of erased-value-arg: an erased value of generic type is returned live.
type Flag is Data:
  Off{}
  On{}

def leak(-A: Type, -w: A) -> A:
  w

def main() -> Flag:
  leak(Flag, On{})

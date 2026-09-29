# A parameter's name shadows the type of that name in the annotations that follow, its own
# included: the seed reads `Flag: Flag` as a variable where a type is due.
type Flag is Data:
  Off{}
  On{}

def f(+Flag: Flag) -> Flag:
  On{}

def main() -> Flag:
  f(On{})

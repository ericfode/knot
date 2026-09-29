# A later parameter's annotation reads the shadowing parameter too.
type Flag is Data:
  Off{}
  On{}

type Other is Data:
  O1{}

def f(Flag: Other, y: Flag) -> Flag:
  y

def main() -> Flag:
  f(O1{}, On{})

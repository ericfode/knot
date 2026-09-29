# And so does the result type.
type Flag is Data:
  Off{}
  On{}

type Other is Data:
  O1{}

def f(Flag: Other) -> Flag:
  On{}

def main() -> Flag:
  f(O1{})

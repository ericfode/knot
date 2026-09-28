type Flag is Data:
  Off{}
  On{}

def identity(-A: Type, x: A) -> A:
  -Alias = A
  x

def main() -> Flag:
  identity(Flag,On{})

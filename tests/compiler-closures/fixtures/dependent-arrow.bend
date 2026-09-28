# A closure parameter with an erased dependent binder, @-A: Type -> A -> A, used at one instance.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}
  Blue{}

def poly(f: @-A: Type -> A -> A, x: Flag) -> Flag:
  f(Flag, x)

def run(x: Flag) -> Flag:
  poly(A => y => y, x)

def main() -> Flag:
  run(On{})

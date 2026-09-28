# An erased value argument is type-checked but never run; erased uses consume nothing.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}
  Blue{}

def ghost(-A: Type, -w: A, x: Flag) -> Flag:
  x

def gate(x: Flag, c: Color) -> Color:
  match x:
    case Off{}:
      Red{}
    case On{}:
      c

def spend(x: Flag, c: Color) -> Color:
  gate(ghost(Color, c, ghost(Color, c, x)), c)

def main() -> Color:
  spend(On{}, Blue{})

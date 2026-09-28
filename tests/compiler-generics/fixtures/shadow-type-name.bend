# A type parameter named Flag shadows the datatype Flag inside pick.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}
  Blue{}

def pick(-Flag: Type, x: Flag) -> Flag:
  x

def paint(c: Color) -> Color:
  pick(Color, c)

def main() -> Color:
  paint(Blue{})

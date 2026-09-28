# A destructured affine field is used twice.
import Base

type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

def both(pair: Flag & Color) -> Color & Color:
  (flag,color) = pair
  (color,color)

def main() -> Color:
  Red{}

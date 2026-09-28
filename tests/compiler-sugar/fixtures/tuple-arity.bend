# A three-name tuple pattern destructures a two-component pair.
import Base

type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

def mid(t: Flag & Color) -> Color:
  (a,c,b) = t
  c

def main() -> Color:
  mid((On{},Blue{}))

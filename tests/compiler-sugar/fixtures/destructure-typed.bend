# A destructuring let carries a type annotation.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

type Pen is Type:
  Pen{flag: Flag, color: Color}

def hue(pen: Pen) -> Color:
  Pen{flag,color} : Pen = pen
  color

def main() -> Color:
  hue(Pen{On{},Blue{}})

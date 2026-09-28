# A constructor destructuring let, Pen{flag,color} = pen, with a promoted field.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

type Pen is Type:
  Pen{flag: Flag, color: Color}

def pick(a: Color, b: Color) -> Color:
  match a:
    case Red{}: Red{}
    case Blue{}: b

def hue(pen: Pen) -> Color:
  Pen{flag,color} = pen
  color

def mark(pen: Pen) -> Flag:
  Pen{flag,color} = pen
  flag

def twice(pen: Pen) -> Color:
  Pen{flag,+color} = pen
  pick(color,color)

def hue_of(f: Flag, c: Color) -> Color:
  hue(Pen{f,c})

def mark_of(f: Flag, c: Color) -> Flag:
  mark(Pen{f,c})

def twice_of(f: Flag, c: Color) -> Color:
  twice(Pen{f,c})

def main() -> Color:
  hue_of(On{},Blue{})

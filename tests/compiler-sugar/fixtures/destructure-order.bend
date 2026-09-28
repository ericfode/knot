# After destructuring a parameter, an earlier parameter is matched.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

type Pen is Type:
  Pen{flag: Flag, color: Color}

def gate(g: Flag, pen: Pen) -> Color:
  Pen{flag,color} = pen
  match g:
    case On{}: color
    case Off{}: Red{}

def main() -> Color:
  gate(On{},Pen{On{},Blue{}})

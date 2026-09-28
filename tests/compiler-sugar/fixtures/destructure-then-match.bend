# A destructuring let is a match: a later parameter and its own fields stay matchable.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

type Pen is Type:
  Pen{flag: Flag, color: Color}

def gate(pen: Pen, g: Flag) -> Color:
  Pen{flag,color} = pen
  match g:
    case On{}: color
    case Off{}: Red{}

def field(pen: Pen) -> Color:
  Pen{flag,color} = pen
  match flag:
    case On{}: color
    case Off{}: Red{}

def gate_of(f: Flag, c: Color, g: Flag) -> Color:
  gate(Pen{f,c},g)

def field_of(f: Flag, c: Color) -> Color:
  field(Pen{f,c})

def main() -> Color:
  gate_of(Off{},Blue{},On{})

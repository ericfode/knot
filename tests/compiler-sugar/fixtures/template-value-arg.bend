# A ~ value parameter: each closed argument makes its own first-order instance.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

def tint(~c: Color, f: Flag) -> Color:
  match f:
    case Off{}: Red{}
    case On{}: c

def pair(a: Color, b: Color) -> Color:
  match a:
    case Red{}: b
    case Blue{}: Blue{}

def blue(f: Flag) -> Color:
  tint(~Blue{},f)

def mixed(f: Flag, g: Flag) -> Color:
  pair(tint(~Red{},f),tint(~Blue{},g))

def main() -> Color:
  mixed(On{},On{})

# A template calls a template declared below it.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

def light(~c: Color, f: Flag) -> Color:
  tint(~c,f)

def tint(~c: Color, f: Flag) -> Color:
  match f:
    case Off{}: Red{}
    case On{}: c

def main() -> Color:
  light(~Blue{},On{})

# A template call may omit every ~: tint(Blue{},f) is the instance at Blue{}.
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

def blue(f: Flag) -> Color:
  tint(Blue{},f)

def main() -> Color:
  blue(On{})

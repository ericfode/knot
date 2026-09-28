# A destructuring let whose value is a call.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

type Pen is Type:
  Pen{flag: Flag, color: Color}

def make(f: Flag) -> Pen:
  Pen{f,Blue{}}

def hue(f: Flag) -> Color:
  Pen{flag,color} = make(f)
  color

def main() -> Color:
  hue(On{})

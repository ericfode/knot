# A Maybe-like option: or_else drops the default when a value is present.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}
  Blue{}

type Opt<-A: Type> is Type:
  Nope{}
  Yep{value: A}

def or_else(-A: Type, o: Opt<A>, d: A) -> A:
  match o:
    case Nope{}:
      d
    case Yep{v}:
      v

def guard(x: Flag, c: Color) -> Opt<Color>:
  match x:
    case Off{}:
      Nope{}
    case On{}:
      Yep{c}

def pick(x: Flag, c: Color) -> Color:
  or_else(Color, guard(x, c), Green{})

def main() -> Color:
  pick(On{}, Blue{})

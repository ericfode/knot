# A closure at a rigid arrow is still affine: twice applies f: A -> A two times.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

def compose(-A: Type, -B: Type, -C: Type, f: A -> B, g: B -> C) -> A -> C:
  x => g(f(x))

def twice(-A: Type, f: A -> A, x: A) -> A:
  f(f(x))

def invert(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def keep(x: Flag) -> Flag:
  x

def paint(f: Flag) -> Color:
  match f:
    case Off{}: Red{}
    case On{}: Blue{}

def tone(c: Color) -> Flag:
  match c:
    case Red{}: On{}
    case Blue{}: Off{}

def select(x: Flag) -> Flag -> Flag:
  match x:
    case Off{}: keep
    case On{}: invert

def round(x: Flag) -> Flag:
  compose(Flag,Color,Flag,paint,tone)(x)

def dispatch(x: Flag, y: Flag) -> Flag:
  compose(Flag,Flag -> Flag,Flag,select,h => h(y))(x)

def nested(x: Flag) -> Color:
  compose(Flag,Flag,Color,compose(Flag,Color,Flag,paint,tone),paint)(x)

def main() -> Flag:
  twice(Flag,invert,On{})

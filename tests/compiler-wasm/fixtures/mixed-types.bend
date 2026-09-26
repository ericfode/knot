type Flag is Type:
  Off{}
  On{}
type Color is Data:
  Red{}
  Green{}
  Blue{}

def choose(-ghost: Flag, x: Flag, +color: Color) -> Color:
  match x:
    case Off{}: color
    case On{}: Blue{}

def main() -> Color:
  choose(Off{},Off{},Green{})

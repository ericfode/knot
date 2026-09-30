type Flag is Data:
  Off{}
  On{}

def flip(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def step0(x: Flag) -> Flag:
  x

def main() -> Flag:
  step0(On{})

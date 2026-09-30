type Flag is Data:
  Off{}
  On{}

def flip(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def step0(x: Flag) -> Flag:
  x

def step1(x: Flag) -> Flag:
  step0(flip(x))

def main() -> Flag:
  step1(On{})

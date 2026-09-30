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

def step2(x: Flag) -> Flag:
  step1(flip(x))

def main() -> Flag:
  step2(On{})

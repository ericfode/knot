def wrap(x: Flag) -> Box<Flag>:
  b: Box<Flag> = Box{x}
  b

type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{value: A}

def open(b: Box<Flag>) -> Flag:
  match b:
    case Box{v}:
      v

def round(x: Flag) -> Flag:
  open(wrap(x))

def main() -> Flag:
  round(On{})

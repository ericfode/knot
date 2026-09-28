type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{value: A}

def open(b: Box<Flag>) -> Flag:
  match b:
    case Box{v}:
      v

def wrap(x: Flag) -> Box<Flag >:
  Box{x}

def main() -> Flag:
  open(wrap(On{}))

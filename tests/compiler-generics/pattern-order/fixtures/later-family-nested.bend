type Flag is Data:
  Off{}
  On{}

def pick(-A: Type, f: Flag, b: Box<A>, d: A) -> A:
  match f:
    case Off{}:
      d
    case On{}:
      match b:
        case Box{v}:
          v

type Box<-A: Type> is Type:
  Box{value: A}

def main() -> Flag:
  pick(Flag, On{}, Box{On{}}, Off{})

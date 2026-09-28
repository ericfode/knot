def flip(x: Flag) -> Flag:
  match x:
    case Off{}:
      On{}
    case On{}:
      Off{}

def main() -> Flag:
  flip(On{})

type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type:
  Box{value: A}

type Tag<-A: Type> is Data:
  First{}
  Second{}

def pick(x: Flag) -> Tag<Flag>:
  match x:
    case Off{}:
      First{}
    case On{}:
      Second{}

def main() -> Tag<Flag>:
  pick(On{})

type Flag is Data:
  Off{}
  On{}

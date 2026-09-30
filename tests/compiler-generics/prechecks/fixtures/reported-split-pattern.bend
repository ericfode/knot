type Flag is Data:
  Off{}
  On{}

type Tag<-A: Type> is Data:
  First{}
  Second{}

type Box<-A: Type> is Type:
  Box{value: A}

def unbox(-A: Type, b: Box<A>) -> A:
  match b:
    case Box{v}:
      v

def pick(x: Flag) -> Tag<Flag>:
  match x:
    case Off{}:
      First{}
    case On{}:
      Second{}

def back(t: Tag<Flag>) -> Flag:
  match t:
    case First{}:
      Off{}
    case Second{}:
      On{}

def rebuild(t: Tag<Flag>) -> Flag:
  match t:
    case First{}:
      back(t)
    case Second{}:
      back(t)

def keep(-A: Type, t: Tag<A>) -> Tag<A>:
  match t:
    case First{}:
      t
    case Second
  {}:
      t

def direct(x: Flag) -> Flag:
  back(pick(x))

def boxed(x: Flag) -> Flag:
  back(unbox(Tag<Flag>, Box{pick(x)}))

def rebuilt(x: Flag) -> Flag:
  rebuild(pick(x))

def kept(x: Flag) -> Flag:
  back(keep(Flag, pick(x)))

def main() -> Flag:
  kept(On{})

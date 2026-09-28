# A phantom parameter: Tagged<A> stores no A; retag changes only the type index.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}
  Blue{}

type Tagged<-A: Type> is Data:
  Tagged{flag: Flag}

def retag(-A: Type, -B: Type, t: Tagged<A>) -> Tagged<B>:
  match t:
    case Tagged{f}:
      Tagged{f}

def read(-A: Type, t: Tagged<A>) -> Flag:
  match t:
    case Tagged{f}:
      f

def cross(x: Flag) -> Flag:
  read(Color, retag(Flag, Color, Tagged{x}))

def main() -> Flag:
  cross(On{})

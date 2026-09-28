# Negative twin of phantom-type: Tagged<Flag> is not Tagged<Color>, same layout or not.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}
  Blue{}

type Tagged<-A: Type> is Data:
  Tagged{flag: Flag}

def read(-A: Type, t: Tagged<A>) -> Flag:
  match t:
    case Tagged{f}:
      f

def mark(x: Flag) -> Tagged<Flag>:
  Tagged{x}

def cross(x: Flag) -> Flag:
  read(Color, mark(x))

def main() -> Flag:
  cross(On{})

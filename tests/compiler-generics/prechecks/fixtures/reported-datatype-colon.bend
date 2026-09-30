type Flag is Data:
  Off{}
  On{}

type Box<-A: Type> is Type # c
  :
  Box{later: A}

def ghost(-p: Flag, x: Flag) -> Flag:
  x

def early(x: Flag) -> Flag:
  ghost(later(main), x)

def later(x: Flag) -> Flag:
  x

def main() -> Flag:
  early(On{})

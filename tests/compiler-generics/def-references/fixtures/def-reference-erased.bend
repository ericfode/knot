type Flag is Data:
  Off{}
  On{}

def ghost(-p: Flag, x: Flag) -> Flag:
  x

def one() -> Flag:
  On{}

def main() -> Flag:
  ghost(one, Off{})

type Box<-A: Type> is Type:
  Box{value: A}

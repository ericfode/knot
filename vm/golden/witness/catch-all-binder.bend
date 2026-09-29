import Base

type Flag is Data:
  Off{}
  On{}

def g(x: Flag) -> Flag:
  match x:
    case y: y

def main() -> Flag:
  g(Off{})

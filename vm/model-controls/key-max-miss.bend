import Base

type Flag is Data:
  Off{}
  On{}

def top(x: U32) -> Flag:
  match x:
    case 4294967295: On{}
    case _: Off{}

def main() -> Flag:
  top(4294967294)

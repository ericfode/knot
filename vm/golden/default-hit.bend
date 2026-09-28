import Base

type Flag is Data:
  Off{}
  On{}

def select(x: U32) -> Flag:
  match x:
    case 7: On{}
    case _: Off{}

def main() -> Flag:
  select(7)

type Flag is Data:
  Off{}
  On{}
def select(x: Flag, y: Flag) -> Flag:
  match x:
    case Off{}:
      value : Flag = y
      value
    case On{}: Off{}
def observe(x: Flag, y: Flag) -> Flag:
  +shadow : Flag = On{}
  select(x,y)
def main() -> Flag:
  observe(Off{},On{})

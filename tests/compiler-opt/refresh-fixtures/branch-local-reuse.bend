type Flag is Data:
  Off{}
  On{}

def choose(x: Flag, +y: Flag) -> Flag:
  match x:
    case On{}:
      +local : Flag = y
      local
    case Off{}:
      +local : Flag = Off{}
      local
def main() -> Flag:
  choose(On{},On{})

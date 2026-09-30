type Flag is Data:
  Off{}
  On{}

def choose(x: Flag, y: Flag) -> Flag:
  x : Flag = y
  +y : Flag = Off{}
  x
def main() -> Flag:
  x : Flag = Off{}
  y : Flag = On{}
  choose(x,y)

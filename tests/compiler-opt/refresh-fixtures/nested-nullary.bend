type Flag is Data:
  Off{}
  On{}

def leaf() -> Flag:
  a : Flag = Off{}
  b : Flag = On{}
  b
def middle(x: Flag) -> Flag:
  a : Flag = x
  leaf()
def main() -> Flag:
  a : Flag = Off{}
  middle(a)

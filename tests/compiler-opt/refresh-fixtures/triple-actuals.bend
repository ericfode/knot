type Flag is Data:
  Off{}
  On{}

def middle(a: Flag, b: Flag, c: Flag) -> Flag:
  b
def local(x: Flag) -> Flag:
  x : Flag = x
  x
def main() -> Flag:
  middle(local(Off{}),local(On{}),local(Off{}))

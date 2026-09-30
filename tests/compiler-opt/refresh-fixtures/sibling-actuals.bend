type Flag is Data:
  Off{}
  On{}

def second(x: Flag, y: Flag) -> Flag:
  y
def local(x: Flag) -> Flag:
  same : Flag = x
  same
def main() -> Flag:
  second(local(Off{}),local(On{}))

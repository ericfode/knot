type Flag is Data:
  Off{}
  On{}

def choose(a: Flag, -b: Flag, c: Flag) -> Flag:
  c
def identity(x: Flag) -> Flag:
  x
def main() -> Flag:
  choose(Off{},identity(Off{}),On{})

type Flag is Type:
  Off{}
  On{}

def take(-x: Flag, y: Flag) -> Flag:
  y
def f(x: Flag) -> Flag:
  take(x,x)
def main() -> Flag:
  f(On{})

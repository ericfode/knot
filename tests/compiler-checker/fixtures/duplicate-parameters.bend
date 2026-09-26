type Flag is Type:
  Off{}
  On{}

def f(x: Flag, x: Flag) -> Flag:
  x
def main() -> Flag:
  f(Off{},On{})

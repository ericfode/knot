type Flag is Type:
  Off{}
  On{}
def f(-x: Flag) -> Flag:
  -y = x
  On{}
def main() -> Flag:
  f(Off{})

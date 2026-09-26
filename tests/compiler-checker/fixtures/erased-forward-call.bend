type Flag is Type:
  Off{}
  On{}

def take(-x: Flag, y: Flag) -> Flag:
  y
def f() -> Flag:
  take(later(),On{})
def later() -> Flag:
  Off{}
def main() -> Flag:
  f()

type Flag is Type:
  Off{}
  On{}
def identity(x: Flag) -> Flag:
  x
def main() -> Flag:
  identity()

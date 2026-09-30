type Flag is Data:
  Off{}
  On{}

def identity(x: Flag) -> Flag:
  x
def main() -> Flag:
  +unused : Flag = Off{}
  +used : Flag = On{}
  identity(used)

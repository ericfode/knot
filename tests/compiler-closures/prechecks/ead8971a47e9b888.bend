type Flag is Data:
  Off{}
  On{}

def main() -> Flag:
  x: Flag<Flag = On{}
  x

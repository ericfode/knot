type Flag is Data:
  Off{}
  On{}
def choose(x: Flag) -> Flag:
  +unused : Flag = Off{}
  +used : Flag = x
  used
def main() -> Flag:
  choose(On{})

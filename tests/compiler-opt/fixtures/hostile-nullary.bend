type Flag is Data:
  Off{}
  On{}

def fixed() -> Flag:
  x : Flag = On{}
  x

def choose(+input: Flag) -> Flag:
  fixed()

def main() -> Flag:
  choose(Off{})

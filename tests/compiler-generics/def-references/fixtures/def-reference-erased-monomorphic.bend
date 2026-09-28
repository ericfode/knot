type Flag is Data:
  Off{}
  On{}

def ghost(-p: Flag, x: Flag) -> Flag:
  x

def one() -> Flag:
  On{}

def main() -> Flag:
  ghost(one, Off{})

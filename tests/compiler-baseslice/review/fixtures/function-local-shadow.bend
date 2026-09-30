type Flag is Data:
  Off{}
  On{}

type Answer is Data:
  No{}
  Yes{}

def flip(x: Flag) -> Flag:
  x

def main() -> Flag:
  flip : Flag = On{}
  flip

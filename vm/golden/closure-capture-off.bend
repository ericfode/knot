type Flag is Data:
  Off{}
  On{}

def capture(k: Flag) -> Flag:
  f : Flag -> Flag = x => k
  f(Off{})

def main() -> Flag:
  capture(Off{})

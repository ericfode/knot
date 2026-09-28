type Flag is Data:
  Off{}
  On{}

type Mark<-A: Type, -f: Flag> is Type:
  Mark{}

def take(x: Mark<Flag, Off{}>) -> Flag:
  On{}

def main() -> Flag:
  take(Mark{})

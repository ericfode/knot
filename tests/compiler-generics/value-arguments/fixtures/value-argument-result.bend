type Flag is Data:
  Off{}
  On{}

type Tag<-f: Flag> is Type:
  Tag{}

def make() -> Tag<On{}>:
  Tag{}

def main() -> Flag:
  On{}

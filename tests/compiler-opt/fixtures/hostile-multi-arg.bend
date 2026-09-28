type Flag is Data:
  Off{}
  On{}

def id(+x: Flag) -> Flag:
  x

def first(+x: Flag, +y: Flag) -> Flag:
  x

def main() -> Flag:
  first(id(Off{}), id(On{}))

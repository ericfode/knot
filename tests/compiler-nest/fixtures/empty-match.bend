# A match with no rows on an inhabited type covers nothing.
type Flag is Data:
  Off{}
  On{}

def void(x: Flag) -> Flag:
  match x:

def main() -> Flag:
  void(On{})

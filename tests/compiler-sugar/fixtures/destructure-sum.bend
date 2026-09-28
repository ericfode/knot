# A destructuring let names one constructor of a two-constructor type.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

def hue(f: Flag) -> Color:
  On{} = f
  Blue{}

def main() -> Color:
  hue(On{})

type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Blue{}

def keep(-w: Color, x: Flag) -> Flag:
  x

def hold(-w: Color, x: Flag) -> Color -> Flag:
  y => keep(w, x)

def run(x: Flag) -> Flag:
  hold(Red{}, x)(Blue{})

def main() -> Flag:
  run(On{})

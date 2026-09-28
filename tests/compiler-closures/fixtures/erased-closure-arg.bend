# Erased positions consume nothing: an erased lambda captures a value also used live, and a closure uses its erased capture only in erased positions.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}
  Blue{}

def ghost(-f: Flag -> Flag, x: Flag) -> Flag:
  x

def keep(-w: Flag, c: Color) -> Color:
  c

def run(x: Flag) -> Flag:
  ghost(y => x, x)

def hold(-w: Flag) -> Color -> Color:
  y => keep(w, y)

def run_hold(x: Flag, c: Color) -> Color:
  hold(x)(c)

def main() -> Flag:
  run(On{})

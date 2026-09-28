# Erased parameters interleaved with live ones; only live positions carry values.
type Flag is Data:
  Off{}
  On{}

type Color is Data:
  Red{}
  Green{}
  Blue{}

def pick_b(x: Flag, -A: Type, y: A, -B: Type, z: B) -> B:
  z

def pick_a(x: Flag, -A: Type, y: A, -B: Type, z: B) -> A:
  y

def last(x: Flag, c: Color, y: Flag) -> Flag:
  pick_b(x, Color, c, Flag, y)

def middle(x: Flag, c: Color, y: Flag) -> Color:
  pick_a(x, Color, c, Flag, y)

def main() -> Color:
  middle(Off{}, Green{}, On{})

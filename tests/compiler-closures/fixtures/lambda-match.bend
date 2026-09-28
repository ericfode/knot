# The seed's lambda-match \{K: arm; ...} is a closure whose body matches its argument.
type Flag is Data:
  Off{}
  On{}

def apply(f: Flag -> Flag, x: Flag) -> Flag:
  f(x)

def run(x: Flag) -> Flag:
  apply(\{On: Off{}; Off: On{}}, x)

def main() -> Flag:
  run(On{})

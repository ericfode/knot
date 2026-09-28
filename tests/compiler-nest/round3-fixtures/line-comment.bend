type Flag is Data:
  Off{}
  On{}

def f(x: Flag, y: Flag) -> Flag:
  match x y: # scrutinees
    case On{} # first column
      # a whole comment line
      On{}: On{}
    case _ _: Off{}

def main() -> Flag:
  f(On{}, On{})

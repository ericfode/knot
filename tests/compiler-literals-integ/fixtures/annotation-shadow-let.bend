# A let binds its name for the body below it, and the seed reads a later annotation that spells that
# name as the variable: `y : Flag` names the let `Flag = x`, not the type.
type Flag is Data:
  Off{}
  On{}

def f(+x: Flag) -> Flag:
  Flag = x
  y : Flag = x
  On{}

def main() -> Flag:
  f(On{})

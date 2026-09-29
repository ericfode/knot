# Binders named like types are harmless while no annotation below them reads the name, and a let's
# own annotation is read before its name binds: `Flag : Flag = x` is a let of the type Flag.
type Flag is Data:
  Off{}
  On{}

type Other is Data:
  O1{}

def own(+x: Flag) -> Flag:
  Flag : Flag = x
  Flag

def other(+x: Flag) -> Flag:
  Flag = x
  y : Other = O1{}
  Flag

def arm(+x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case Flag:
      y : Other = O1{}
      Flag

def main() -> Flag:
  arm(other(own(On{})))

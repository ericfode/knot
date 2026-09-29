# The seed's scope holds the name of every let, erased or not: a later live let of that name
# binds it, however it is spelled, typed or plain, nested or in an arm.
type Flag is Data:
  Off{}
  On{}

def plain(+x: Flag) -> Flag:
  -a.b = x
  a.b = x
  a.b

def typed(+x: Flag) -> Flag:
  -a.b : Flag = x
  a.b : Flag = x
  a.b

def twice(+x: Flag) -> Flag:
  -a.b = x
  -a.b = x
  a.b = x
  a.b

def deep(+x: Flag) -> Flag:
  -a.b.c = x
  a.b.c = x
  a.b.c

def arm(+x: Flag) -> Flag:
  match x:
    case Off{}:
      -a.b : Flag = x
      a.b : Flag = x
      a.b
    case On{}: x

def main() -> Flag:
  plain(typed(twice(deep(arm(On{})))))

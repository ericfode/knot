# The seed's scope holds the name of every let, erased or live, so a live let of an erased let's
# dotted name binds it: plain after plain, typed after plain, in an arm, and past a second erased let.
type Flag is Data:
  Off{}
  On{}

def plain(x: Flag) -> Flag:
  -a.b = x
  a.b = x
  a.b

def typed(x: Flag) -> Flag:
  -a.b = x
  a.b : Flag = x
  a.b

def arm(x: Flag, p: Flag) -> Flag:
  match p:
    case On{}:
      -a.b = x
      a.b = x
      a.b
    case Off{}: x

def between(x: Flag) -> Flag:
  -a.b = x
  -c.d = x
  c.d = x
  c.d

def main() -> Flag:
  between(arm(typed(plain(On{})), On{}))

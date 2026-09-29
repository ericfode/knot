# An erased let's name is a name, however it is spelled: the seed accepts a dotted one that no
# parameter binds, typed or plain, and the body never reads it.
type Flag is Data:
  Off{}
  On{}

def typed(x: Flag) -> Flag:
  -a.b : Flag = x
  x

def plain(x: Flag) -> Flag:
  -a.b = x
  x

def main() -> Flag:
  plain(typed(On{}))

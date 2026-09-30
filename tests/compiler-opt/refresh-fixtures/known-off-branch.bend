type Flag is Data:
  Off{}
  On{}

def branch(x: Flag) -> Flag:
  match x:
    case On{}:
      y : Flag = x
      y
    case Off{}: Off{}
def main() -> Flag:
  +known : Flag = Off{}
  branch(known)

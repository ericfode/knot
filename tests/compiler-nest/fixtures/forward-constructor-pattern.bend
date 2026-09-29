# Constructor patterns resolve when parsed: On{} before its datatype is unknown.
def flip(x: Flag) -> Flag:
  match x:
    case On{}: Off{}
    case Off{}: On{}

type Flag is Data:
  Off{}
  On{}

def main() -> Flag:
  flip(Off{})

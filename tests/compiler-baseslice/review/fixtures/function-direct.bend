type Flag is Data:
  Off{}
  On{}

type Answer is Data:
  No{}
  Yes{}

def Flag.not(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

def main() -> Flag:
  Flag.not(Off{})

# Before Flag is declared, the bare name On is a binder for the scrutinee.
def same(x: Flag) -> Flag:
  match x:
    case On: On

type Flag is Data:
  Off{}
  On{}

def main() -> Flag:
  same(Off{})

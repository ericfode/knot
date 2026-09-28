type Flag is Type:
  Off{}
  On{}

def f(x: Flag) -> Flag:
  match x:
    case Off: On{}

type Light is Type:
  Dark{}
  Lit{}

def see(x: Flag) -> Light:
  match x:
    case Off{}: Dark{}
    case On{}: Lit{}

def main() -> Light:
  see(f(Off{}))

type Flag is Type:
  Off{}
  On{}

type Mark is Type:
  Unit0{}

type Box is Type:
  Box{v: Flag}

def open(b: Box) -> Flag:
  match b:
    case Box{Mark}: Mark

type Other is Type:
  Mark{}

type Light is Type:
  Dark{}
  Lit{}

def see(x: Flag) -> Light:
  match x:
    case Off{}: Dark{}
    case On{}: Lit{}

def main() -> Light:
  see(open(Box{On{}}))

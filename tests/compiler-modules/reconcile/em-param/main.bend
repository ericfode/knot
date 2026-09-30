import ./lib/v.bend as V

type Light is Type:
  Dark{}
  Lit{}

def see(x: V.Flag) -> Light:
  match x:
    case V.Off{}: Dark{}
    case V.On{}: Lit{}

def main() -> Light:
  see(V.On{})

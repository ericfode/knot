import ./lib/chain/one.bend as One

type Light is Type:
  Dark{}
  Lit{}

def see(x: One.Hop) -> Light:
  match x:
    case One.Near{}: Lit{}
    case One.Far{}: Dark{}

def main() -> Light:
  see(One.lift())

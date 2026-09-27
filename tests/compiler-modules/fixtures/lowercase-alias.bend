import ./lib/flag.bend as f

type Light is Type:
  Dark{}
  Lit{}

def see(x: f.Flag) -> Light:
  match x:
    case f.Off{}: Dark{}
    case f.On{}: Lit{}

def main() -> Light:
  see(f.flip(f.On{}))

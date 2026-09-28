import ./lib/m.bend as M

type Light is Type:
  Dark{}
  Lit{}

def see(x: M.Flag) -> Light:
  match x:
    case M.Off{}: Dark{}
    case M.On{}: Lit{}

def main() -> Light:
  see(M.g(M.P{M.Off{}, M.Off{}}))

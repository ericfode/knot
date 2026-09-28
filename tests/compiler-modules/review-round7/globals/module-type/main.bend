import ./lib/m.bend as M

type Light is Type:
  Dark{}
  Lit{}

def see(x: M.Flag) -> Light:
  match x:
    case M.Off{}: Dark{}
    case M.On{}: Lit{}

def f(x: Light) -> Light:
  T = M.Flag
  y : T = M.On{}
  see(y)

def main() -> Light:
  f(Dark{})

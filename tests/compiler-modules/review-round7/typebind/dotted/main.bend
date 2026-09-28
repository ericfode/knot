import ./lib/m.bend as M

type Light is Type:
  Dark{}
  Lit{}

def g(M.Flag: M.Flag, x: M.Flag) -> Light:
  Lit{}

def main() -> Light:
  g(M.On{}, M.Off{})

# Blank and comment lines may precede imports.

import ./lib/flag.bend as F # a trailing comment ends the import line

type Light is Type:
  Dark{}
  Lit{}

def see(x: F.Flag) -> Light:
  match x:
    case F.Off{}: Dark{}
    case F.On{}: Lit{}

def main() -> Light:
  see(F.On{})

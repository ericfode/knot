# A Char literal is compared where a U32 is expected.
import Base

type Mode is Data:
  Space{}
  Comment{}

def verdict(b: Bool, +yes: Mode, +no: Mode) -> Mode:
  match b:
    case True{}: yes
    case False{}: no

def step(+c: Char) -> Mode:
  verdict(U32.is_eq(Char.to_u32(c),'\n'),Space{},Comment{})

def main() -> Mode:
  Space{}

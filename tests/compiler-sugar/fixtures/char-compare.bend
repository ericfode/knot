# The lex.step_at shape: Char.is_eq(c,'\n') on a reusable Char, beside Char.to_u32.
import Base

type Glyph is Data:
  Newline{}
  Letter{}
  Tilde{}

type Mode is Data:
  Space{}
  Comment{}
  Ident{}

def glyph(g: Glyph) -> Char:
  match g:
    case Newline{}: '\n'
    case Letter{}: 'n'
    case Tilde{}: Char.from_u32(126)

def verdict(b: Bool, +yes: Mode, +no: Mode) -> Mode:
  match b:
    case True{}: yes
    case False{}: no

def step(+c: Char) -> Mode:
  verdict(Char.is_eq(c,'\n'),Space{},verdict(U32.is_gt(Char.to_u32(c),125),Comment{},Ident{}))

def after(g: Glyph) -> Mode:
  step(glyph(g))

def main() -> Mode:
  after(Newline{})

# Char literal patterns, including an escape, with a wildcard default.
import Base

type Class is Type:
  Letter{}
  Break{}
  Other{}

type Glyph is Type:
  GA{}
  GB{}
  GNewline{}

def char(g: Glyph) -> Char:
  match g:
    case GA{}: 'a'
    case GB{}: 'b'
    case GNewline{}: '\n'

def class(c: Char) -> Class:
  match c:
    case 'a': Letter{}
    case '\n': Break{}
    case _: Other{}

def classify(g: Glyph) -> Class:
  class(char(g))

def main() -> Class:
  classify(GNewline{})

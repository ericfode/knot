# Local module for qualified-collision: `pick` calls this module's own generic
# `select`; the entry declares another `select` with another signature.
import Base

type Color is Data:
  Red{}
  Green{}
  Blue{}

type Flag is Data:
  Off{}
  On{}

def select(-A: Type, c: Flag, a: A, b: A) -> A:
  match c:
    case Off{}: a
    case On{}: b

def pick(c: Flag, x: Color, y: Color) -> Color:
  select(Color,c,x,y)

# The narrow row's literal may sit in a constructor's field.
import Base

type Answer is Type:
  No{}
  Yes{}

type Box is Data:
  Bx{v: U32}

def f(a: Box, b: Box) -> Answer:
  match a b:
    case Bx{0}: Yes{}
    case _ _: No{}

def main() -> Answer:
  f(Bx{0}, Bx{1})

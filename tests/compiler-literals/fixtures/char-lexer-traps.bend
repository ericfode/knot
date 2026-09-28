# Char literals of quote, hash and space characters: ''' is an apostrophe.
import Base

type Answer is Type:
  No{}
  Yes{}

type Trap is Data:
  Apostrophe{}
  DoubleQuote{}
  Hash{}
  Space{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def char(t: Trap) -> Char:
  match t:
    case Apostrophe{}: '''
    case DoubleQuote{}: '"'
    case Hash{}: '#'
    case Space{}: ' '

def code(t: Trap) -> U32:
  match t:
    case Apostrophe{}: 39
    case DoubleQuote{}: 34
    case Hash{}: 35
    case Space{}: 32

def exact(+t: Trap) -> Answer:
  verdict(U32.is_eq(Char.to_u32(char(t)), code(t)))

def is_space(t: Trap) -> Answer:
  verdict(Char.is_space(char(t)))

def main() -> Answer:
  exact(Apostrophe{})

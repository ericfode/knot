# Char escapes \n \t \r \0 \\ \' \" denote their code points.
import Base

type Answer is Type:
  No{}
  Yes{}

type Escape is Data:
  Newline{}
  Tab{}
  Return{}
  Nul{}
  Backslash{}
  Quote{}
  DoubleQuote{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def char(e: Escape) -> Char:
  match e:
    case Newline{}: '\n'
    case Tab{}: '\t'
    case Return{}: '\r'
    case Nul{}: '\0'
    case Backslash{}: '\\'
    case Quote{}: '\''
    case DoubleQuote{}: '\"'

def code(e: Escape) -> U32:
  match e:
    case Newline{}: 10
    case Tab{}: 9
    case Return{}: 13
    case Nul{}: 0
    case Backslash{}: 92
    case Quote{}: 39
    case DoubleQuote{}: 34

def exact(+e: Escape) -> Answer:
  verdict(U32.is_eq(Char.to_u32(char(e)), code(e)))

def is_space(e: Escape) -> Answer:
  verdict(Char.is_space(char(e)))

def main() -> Answer:
  exact(Nul{})

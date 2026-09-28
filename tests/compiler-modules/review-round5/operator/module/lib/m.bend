import Base

type Flag is Type:
  Off{}
  On{}

def drop(p: Flag & Flag) -> Flag:
  On{}

def flip(x: Flag) -> Flag:
  match x:
    case Off{}: On{}
    case On{}: Off{}

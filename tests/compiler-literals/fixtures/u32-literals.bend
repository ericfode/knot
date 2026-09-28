# Decimal U32 literals: zero, the maximum, and leading zeros (007 is seven).
import Base

type Answer is Type:
  No{}
  Yes{}

type Pick is Type:
  Low{}
  Mid{}
  High{}

def verdict(b: Bool) -> Answer:
  match b:
    case False{}: No{}
    case True{}: Yes{}

def value(p: Pick) -> U32:
  match p:
    case Low{}: 0
    case Mid{}: 007
    case High{}: 4294967295

def is_max(p: Pick) -> Answer:
  verdict(U32.is_eq(value(p), U32.not(0)))

def is_seven(p: Pick) -> Answer:
  verdict(U32.is_eq(value(p), 7))

def main() -> Answer:
  is_max(High{})

# Overlapping U32 patterns: the first matching arm wins.
import Base

type Answer is Type:
  No{}
  Yes{}

type Pick is Type:
  Nought{}
  One{}

def value(p: Pick) -> U32:
  match p:
    case Nought{}: 0
    case One{}: 1

def repeated(x: U32) -> Answer:
  match x:
    case 0: Yes{}
    case 0: No{}
    case _: No{}

def shadowed(x: U32) -> Answer:
  match x:
    case _: No{}
    case 0: Yes{}

def first_arm(p: Pick) -> Answer:
  repeated(value(p))

def wildcard_first(p: Pick) -> Answer:
  shadowed(value(p))

def main() -> Answer:
  first_arm(Nought{})

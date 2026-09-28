# U32 literal patterns with a binder default that receives the scrutinee.
import Base

type Band is Type:
  Bare{}
  Single{}
  Seven{}
  Full{}
  Other{}

type Mark is Type:
  N0{}
  N1{}
  N7{}
  N8{}
  NMax{}

def value(m: Mark) -> U32:
  match m:
    case N0{}: 0
    case N1{}: 1
    case N7{}: 7
    case N8{}: 8
    case NMax{}: 4294967295

def rest(b: Bool) -> Band:
  match b:
    case False{}: Other{}
    case True{}: Seven{}

def band(x: U32) -> Band:
  match x:
    case 0: Bare{}
    case 1: Single{}
    case 4294967295: Full{}
    case n: rest(U32.is_eq(n, 7))

def classify(m: Mark) -> Band:
  band(value(m))

def main() -> Band:
  classify(N7{})

import Base

# Unary arithmetic on a user datatype: no word Nat, no primitive on the hot path.
type Peano is Data:
  Z{}
  S{pred: Peano}

def add(a: Peano, b: Peano) -> Peano:
  match a:
    case Z{}: b
    case S{p}: S{add(p,b)}

def mul(a: Peano, +b: Peano) -> Peano:
  match a:
    case Z{}: Z{}
    case S{p}: add(b,mul(p,b))

def peano(n: Nat) -> Peano:
  match n:
    case 0n: Z{}
    case 1n+p: S{peano(p)}

def count(a: Peano, n: U32) -> U32:
  match a:
    case Z{}: n
    case S{p}: count(p,U32.add(n,1))

# Each round builds and consumes a fresh 10^6-node product.
def rounds(k: Nat, total: U32) -> U32:
  match k:
    case 0n: total
    case 1n+p: rounds(p,U32.add(total,count(mul(peano(1000n),peano(1000n)),0)))

def main() -> Bool:
  U32.is_eq(rounds(40n,0),40000000)

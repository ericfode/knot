import Base

def build(n: Nat, +next: U32, acc: List<&2,U32>) -> List<&2,U32>:
  match n:
    case 0n: acc
    case 1n+p: build(p,U32.add(next,1),Con{next,acc})

def fold(xs: List<&2,U32>, total: U32) -> U32:
  match xs:
    case Nil{}: total
    case Con{x,rest}: fold(rest,U32.add(total,x))

def rounds(k: Nat, total: U32) -> U32:
  match k:
    case 0n: total
    case 1n+p: rounds(p,U32.add(total,fold(build(1000000n,1,Nil{}),0)))

# Each round sums 1..1000000 modulo 2^32 (1784293664); 240 rounds give 3028717056.
def main() -> Bool:
  U32.is_eq(rounds(12n,0),4231654784)

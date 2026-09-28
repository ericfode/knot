import Base

# 250,000 pending additions: every frame waits for its callee.
def depth(n: Nat) -> U32:
  match n:
    case 0n: 0
    case 1n+p: U32.add(depth(p),1)

def rounds(k: Nat, total: U32) -> U32:
  match k:
    case 0n: total
    case 1n+p: rounds(p,U32.add(total,depth(250000n)))

def main() -> Bool:
  U32.is_eq(rounds(400n,0),100000000)

import Base

def letter(+i: U32) -> Char:
  Char.from_u32(U32.add(97,U32.mod(i,26)))

# One SCon cell per character, built back to front.
def build(n: Nat, +i: U32, acc: String) -> String:
  match n:
    case 0n: acc
    case 1n+p: build(p,U32.add(i,1),SCon{letter(i),acc})

# Every round builds a fresh 10,000-character string and scans it against the fixed one.
def rounds(k: Nat, +fixed: String, hits: U32) -> U32:
  match k:
    case 0n: hits
    case 1n+p: rounds(p,fixed,U32.add(hits,Bool.pick(U32,String.eq(build(10000n,0,""),fixed),1,0)))

def main() -> Bool:
  U32.is_eq(rounds(900n,build(10000n,0,""),0),900)

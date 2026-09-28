import Base

def count(n: Nat, +i: U32) -> IO(Unit):
  match n:
    case 0n: IO.print(String.append("printed ",U32.show(i)))
    case 1n+p: IO.bind(Unit,Unit,IO.print(U32.show(i)),u => count(p,U32.add(i,1)))

def main() -> IO(Unit):
  count(5000n,0)

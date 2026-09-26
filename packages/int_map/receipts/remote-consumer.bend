import Base
import 0x99e32f5f97dad3791a32b01d133555c5/main.bend as M
import 0x99e32f5f97dad3791a32b01d133555c5/release.bend as Remote

def matches(x: Maybe<&2,U32>, expected: U32) -> Bool:
  match x:
    case None{}: False{}
    case Some{v}: U32.is_eq(v,expected)

def checked(ok: Bool) -> IO(Unit):
  match ok:
    case False{}: IO.die(Unit,1,"REMOTE consumer failed")
    case True{}: IO.print("REMOTE snapshot/union=ok")

def consumer() -> IO(Unit):
  +left = M.IntMap.set(U32,M.IntMap.empty(U32),4294967295,7)
  right = M.IntMap.set(U32,M.IntMap.set(U32,M.IntMap.empty(U32),4294967295,6),0,0)
  +result = M.IntMap.union_with(~U32,~(a => b => U32.add(U32.mul(a,100),b)),left,right)
  checked(Bool.and(matches(M.IntMap.get(U32,left,4294967295),7),
    Bool.and(matches(M.IntMap.get(U32,result,4294967295),706),
      Bool.and(matches(M.IntMap.get(U32,result,0),0),Nat.is_eq(M.IntMap.size(U32,result),2n)))))

def main() -> IO(Unit):
  do IO<Unit>:
    Remote.main()
    consumer()

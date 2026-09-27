# SPDX-License-Identifier: MIT-0
import Base
import ./main.bend as M

def total(m: M.IntMap<U32>) -> U32:
  M.IntMap.fold(~U32,~U32,~(acc => key => value => U32.add(acc,value)),m,0)

def main() -> IO(Unit):
  +left = M.IntMap.set(U32,M.IntMap.set(U32,M.IntMap.empty(U32),1,2),2,3)
  +right = M.IntMap.set(U32,M.IntMap.set(U32,M.IntMap.empty(U32),2,7),4294967295,5)
  add = M.IntMap.union_with(~U32,~U32.add,left,right)
  join = M.IntMap.union_with(~U32,~(a => b => U32.max(a,b)),left,right)
  do IO<Unit>:
    IO.print(String.append("add=",U32.show(total(add))))
    IO.print(String.append("join=",U32.show(total(join))))
    IO.print(String.append("previous=",U32.show(total(left))))

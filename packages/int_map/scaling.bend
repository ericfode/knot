# SPDX-License-Identifier: MIT-0
import Base
import ./main.bend as M
import ./fixtures.bend as F
import ./model.bend as Ref

def build(n: Nat, +shift: Nat, m: M.IntMap<U32>) -> M.IntMap<U32>:
  match n:
    case 0n: m
    case 1n+ +p:
      +k = U32.from_nat(p)
      build(p,shift,M.IntMap.set(U32,m,U32.shln(k,shift),U32.add(k,1)))

def model(n: Nat, +shift: Nat, xs: List<&2,Ref.Item<U32>>) -> List<&2,Ref.Item<U32>>:
  match n:
    case 0n: xs
    case 1n+ +p:
      +k = U32.from_nat(p)
      model(p,shift,Ref.set(U32,xs,U32.shln(k,shift),U32.add(k,1)))

def verify(n: Nat, +shift: Nat, +m: M.IntMap<U32>) -> Bool:
  match n:
    case 0n: True{}
    case 1n+ +p:
      +k = U32.from_nat(p)
      Bool.and(F.maybe_eq(M.IntMap.get(U32,m,U32.shln(k,shift)),Some{U32.mul(2,U32.add(k,1))}),verify(p,shift,m))

def erase(n: Nat, +shift: Nat, m: M.IntMap<U32>) -> M.IntMap<U32>:
  match n:
    case 0n: m
    case 1n+ +p: erase(p,shift,M.IntMap.remove(U32,m,U32.shln(U32.from_nat(p),shift)))

def nodes(m: M.IntMap<U32>) -> Nat:
  match m:
    case M.Tip{}: 0n
    case M.Entry{k,v}: 1n
    case M.Branch{lo,hi}: 1n+Nat.add(nodes(lo),nodes(hi))

def depth(m: M.IntMap<U32>) -> Nat:
  match m:
    case M.Tip{}: 0n
    case M.Entry{k,v}: 0n
    case M.Branch{lo,hi}: 1n+Nat.max(depth(lo),depth(hi))

def report(ok: Bool, +n: Nat, shift: Nat, count: Nat, height: Nat, sum: U32) -> IO(Unit):
  match ok:
    case False{}: IO.die(Unit,1,"scaling semantics failed")
    case True{}:
      do IO<Unit>:
        IO.print(String.append("n=",Nat.show(n)))
        IO.print(String.append("shift=",Nat.show(shift)))
        IO.print(String.append("retained_nonempty_nodes=",Nat.show(count)))
        IO.print(String.append("max_key_depth=",Nat.show(height)))
        IO.print(String.append("union_sum=",U32.show(sum)))
        IO.print(String.append("source_set_trie_constructors=",Nat.show(Nat.mul(n,33n))))

def run(+n: Nat, +shift: Nat) -> IO(Unit):
  +m = build(n,shift,M.IntMap.empty(U32))
  +u = M.IntMap.union_with(~U32,~U32.add,m,m)
  +sum = M.IntMap.fold(~U32,~U32,~(acc => key => value => U32.add(acc,value)),u,0)
  +expected_sum = U32.mul(U32.from_nat(n),U32.add(U32.from_nat(n),1))
  report(Bool.and(verify(n,shift,u),Bool.and(U32.is_eq(sum,expected_sum),
    Bool.and(Nat.is_eq(M.IntMap.size(U32,u),n),Bool.and(Nat.is_eq(nodes(erase(n,shift,u)),0n),
      Bool.and(Nat.is_le(depth(m),32n),F.agree(m,model(n,shift,Nil{}))))))),n,shift,nodes(m),depth(m),sum)

def run_core(+n: Nat, +shift: Nat) -> IO(Unit):
  +m = build(n,shift,M.IntMap.empty(U32))
  +u = M.IntMap.union_with(~U32,~U32.add,m,m)
  +sum = M.IntMap.fold(~U32,~U32,~(acc => key => value => U32.add(acc,value)),u,0)
  +expected_sum = U32.mul(U32.from_nat(n),U32.add(U32.from_nat(n),1))
  report(Bool.and(verify(n,shift,u),Bool.and(U32.is_eq(sum,expected_sum),
    Bool.and(Nat.is_eq(M.IntMap.size(U32,u),n),Bool.and(Nat.is_eq(nodes(erase(n,shift,u)),0n),
      Bool.and(Nat.is_le(depth(m),32n),True{}))))),n,shift,nodes(m),depth(m),sum)

# Both layouts require the documented 1..4096 workload domain. Reject outside
# it before conversion/shift or any model construction can start.
def run_checked(+n: Nat, valid: Bool) -> IO(Unit):
  match valid:
    case False{}: IO.die(Unit,2,"expected positive size <=4096")
    case True{}:
      do IO<Unit>:
        run(n,0n)
        run(n,16n)

def parsed(n: Maybe<&2,Nat>) -> IO(Unit):
  match n:
    case None{}: IO.die(Unit,2,"expected positive size <=4096")
    case Some{+n}: run_checked(n,Bool.and(Nat.is_ge(n,1n),Nat.is_le(n,4096n)))

def args(xs: List<String>) -> IO(Unit):
  match xs:
    case Nil{}: parsed(Some{64n})
    case Con{s,tail}: parsed(Nat.read(s))

def main() -> IO(Unit):
  do IO<Unit>:
    xs : List<String> <- IO.args()
    args(xs)

def run_core_checked(+n: Nat, valid: Bool) -> IO(Unit):
  match valid:
    case False{}: IO.die(Unit,2,"expected positive size <=4096")
    case True{}:
      do IO<Unit>:
        run_core(n,0n)
        run_core(n,16n)

def parsed_core(n: Maybe<&2,Nat>) -> IO(Unit):
  match n:
    case None{}: IO.die(Unit,2,"expected positive size <=4096")
    case Some{+n}: run_core_checked(n,Bool.and(Nat.is_ge(n,1n),Nat.is_le(n,4096n)))

def args_core(xs: List<String>) -> IO(Unit):
  match xs:
    case Nil{}: parsed_core(Some{64n})
    case Con{s,tail}: parsed_core(Nat.read(s))

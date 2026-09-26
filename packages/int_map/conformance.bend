# SPDX-License-Identifier: MIT-0
import Base
import ./main.bend as M
import ./fixtures.bend as F

def check(ok: Bool, name: String) -> IO(Unit):
  match ok:
    case False{}: IO.die(Unit,1,name)
    case True{}: IO.print(String.append("PASS ",name))

def main() -> IO(Unit):
  do IO<Unit>:
    check(F.boundary(),"boundary/absence/overwrite/removal/persistence")
    check(F.bit_cases(32n,1),"all-32-bits/complements")
    check(F.order_case(),"fold-exact-contents/order")
    check(F.unions(),"noncommutative/add/max/union-identities")
    check(F.trace_case(),"combiner-invocation-tree/order/singletons")
    check(F.union_model(),"independent-union-model")
    check(F.sequence(192n,731,M.IntMap.empty(U32),Nil{}),"192-composed-model-transitions")
    check(F.union_stress(),"96-entry-unions-vs-independent-model")
    check(F.fold_seed_case(),"fold-initial-accumulator/composition")

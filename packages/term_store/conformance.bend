import Base
import ./checks.bend as C
import ./memo_checks.bend as MC
import ./lifecycle.bend as LC
import ./payload.bend as P
import ./data_checks.bend as D
import ./main.bend as S

# Deterministic mixed histories. Arithmetic only chooses tests; oracle is list/state.
def choose_kind(kind: U32,+seed: U32) -> C.Op:
  match kind:
    case 0: C.Alloc{seed}
    case 1: C.Read{S.Id{7,U32.mod(U32.div(seed,5),19)}}
    case 2: C.Write{S.Id{7,U32.mod(U32.div(seed,5),19)},seed}
    case 3: C.Read{S.Id{8,U32.mod(seed,19)}}
    case _: C.Length{}

def choose(+seed: U32) -> C.Op:
  choose_kind(U32.mod(seed,5),seed)

def history(n: Nat,+seed: U32) -> List<&2,C.Op>:
  match n:
    case 0n: [C.Limit{}]
    case 1n+p:
      Con{choose(seed),history(p,U32.add(U32.mul(seed,1664525),1013904223))}

def traces(n: Nat,+seed: U32) -> Bool:
  match n:
    case 0n: True{}
    case 1n+p:
      Bool.and(C.trace(history(128n,seed),7,17),traces(p,U32.add(seed,37)))

def verify(name: String,ok: Bool) -> IO(Unit):
  match ok:
    case False{}: IO.die(Unit,1,String.append("FAIL ",name))
    case True{}: IO.print(String.append("PASS ",name))

def main() -> IO(Unit):
  do IO<Unit>:
    verify("store-values-growth-update-preservation",C.store_witness())
    verify("zero-limit",C.zero_witness())
    verify("first-order-term-payloads",Bool.and(D.store_terms(),D.memo_terms()))
    verify("memo-transition-result-preservation",MC.witness())
    verify("lifetime-separation",LC.separate_lifetimes())
    verify("scope-exhaustion",LC.scope_exhaustion())
    verify("zero-store-consumes-scope",LC.zero_consumes_scope())
    verify("memo-interleaved-growth-and-exhaustion",MC.interleaved_witness())
    verify("limit-clamp",LC.max_limit())
    verify("128-mixed-histories-x128-operations",traces(128n,19))

import Base
import ./syntax.bend as S
import ./core.bend as C

# kn+t: k applications of one unary constructor around the tail, checked once.
def successors(k: Nat, term: C.Term, +token: S.Token, +type_id: U32, +tag: U32, +fields: List<&2,C.Parameter>) -> C.Term:
  match k:
    case 0n: term
    case 1n+p: C.Construct{token,type_id,tag,fields,[successors(p,term,token,type_id,tag,fields)]}

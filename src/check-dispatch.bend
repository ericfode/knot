import Base
import ./syntax.bend as S
import ./core.bend as C
import ./check.bend as K
import ./generics.bend as J

# A book with generic syntax is checked by the generic checker; every other
# book keeps the monomorphic checker and its pinned diagnostics.
def check(depth: Nat, root: S.Node) -> Result<S.Error,C.Book>:
  match depth root:
    case 0n _: Fail{S.Exhausted{"check",S.At{0,0,0,0}}}
    case 1n+ +n S.Sequence{+nodes}:
      S.choose(Result<S.Error,C.Book>,J.required(nodes),u => J.check(1n+n,nodes),u => K.check(1n+n,S.Sequence{nodes}))
    case _ _: C.internal(C.Book,"root-node")

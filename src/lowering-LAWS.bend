import Base
import ./syntax.bend as S
import ./core.bend as C
import ./scope.bend as E
import ./matrix.bend as M

# The complete lowering: every successful expansion of a matrix whose first row
# is irrefutable selects that row. Failures (fuel, work, catalog, scope and
# checking errors) are other outcomes and are not claimed absent.

# A row is irrefutable against its columns when every pattern binds without
# inspection; indexing by the columns rules out a short row, which a split
# would drop. A leaf is what expansion returns unchanged.
def Irrefutable(columns: List<&2,S.Node>, patterns: List<&2,S.Node>) -> Data:
  match columns patterns:
    case Nil{} Nil{}: Unit
    case Con{column,rest} Con{S.Variable{name},tail}: Irrefutable(rest,tail)
    case Con{column,rest} Con{S.Promotion{name},tail}: Irrefutable(rest,tail)
    case _ _: Empty

def Leaf(node: S.Node) -> Data:
  match node:
    case S.Matrix{token,columns,rows,work}: Empty
    case S.Decision{token,column,pattern,yes,no}: Empty
    case S.Alias{token,level,mark,body}: Empty
    case _: Unit

# Aliases are transparent and a decision has two subtrees.
def Leaves(tree: S.Node, body: S.Node) -> Type:
  match tree:
    case S.Alias{token,level,mark,rest}: Leaves(rest,body)
    case S.Decision{token,column,pattern,yes,no}: Leaves(yes,body) & Leaves(no,body)
    case _: {tree == body : S.Node}

law irrefutable_first_row_selected:
  for fuel: Nat
  for +token: S.Token
  for +columns: List<&2,S.Node>
  for +arm: S.Token
  for +patterns: List<&2,S.Node>
  for +body: S.Node
  for +rows: List<&2,S.Node>
  for +quota: U32
  for +types: List<&2,C.Datatype>
  for +scope: E.Scope
  for +work: U32
  for tree: S.Node
  for left: U32
  for irrefutable: Irrefutable(columns,patterns)
  for leaf: Leaf(body)
  for lowered: {M.expand(fuel,S.Matrix{token,columns,Con{S.Arm{arm,S.Sequence{patterns},body},rows},quota},types,scope,work) ==
    Done{M.Expansion{tree,left}} : Result<S.Error,M.Expansion>}
  Leaves(tree,body)

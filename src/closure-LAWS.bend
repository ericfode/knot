import Base
import ./syntax.bend as S
import ./core.bend as C
import ./closure.bend as F

law capture_arity:
  for +captures: List<&2,C.Binding>
  for +rename: F.Rename
  {List.length(&2,C.Term,F.capture_args(captures,rename)) == List.length(&2,C.Binding,captures) : Nat}

law capture_quantity:
  for +token: S.Token
  for level: U32
  for +quantity: U32
  for +typ: U32
  for parameter: Bool
  for known: Maybe<&2,C.Term>
  for +tail: List<&2,C.Binding>
  {F.capture_params(Con{C.Binding{token,level,quantity,typ,parameter,known},tail}) == Con{C.Parameter{token,quantity,typ},F.capture_params(tail)} : List<&2,C.Parameter>}

law close_has_one_cell:
  for +token: S.Token
  for +tag: U32
  for +typ: U32
  for +captures: List<&2,C.Binding>
  for +rename: F.Rename
  {F.pack(token,tag,typ,captures,rename) == C.Construct{token,typ,tag,F.capture_params(captures),F.capture_args(captures,rename)} : C.Term}

law invoke_has_one_dispatch:
  for +token: S.Token
  for +index: U32
  for +result: U32
  for +function: C.Term
  for +argument: C.Term
  {F.apply(token,index,result,function,argument) == C.Application{token,index,result,[function,argument]} : C.Term}

law outer_levels_are_unchanged:
  for +id: U32
  {F.level(F.Same{},id) == id : U32}

law rewrite_exhaustion:
  for term: C.Term
  for rename: F.Rename
  for table: List<&2,F.Dispatch>
  {F.rewrite(0n,term,rename,table) == Fail{S.Exhausted{"emit",S.At{0,0,0,0}}} : Result<S.Error,C.Term>}

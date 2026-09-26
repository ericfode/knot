import Base
import ./syntax.bend as S
import ./core.bend as C
import ./eval.bend as E
import ./wasm-bytes.bend as W

law returned_value_needs_no_fuel:
  for +value: E.Value
  for book: C.Book
  {E.run(0n,E.Return{value,Nil{}},book) == Done{value} : Result<S.Error,E.Value>}

law pending_evaluation_needs_fuel:
  for term: C.Term
  for environment: List<&2,E.Entry>
  for frames: List<&2,E.Frame>
  for book: C.Book
  {E.run(0n,E.Evaluate{term,environment,frames},book) == Fail{S.Exhausted{"eval",S.At{0,0,0,0}}} : Result<S.Error,E.Value>}

law erased_initializer_is_not_evaluated:
  for token: S.Token
  for level: U32
  for type_id: U32
  for initial: C.Term
  for +body: C.Term
  for +environment: List<&2,E.Entry>
  for +frames: List<&2,E.Frame>
  for book: C.Book
  {E.step(E.Evaluate{C.Let{token,level,0,type_id,initial,body},environment,frames},book) == Done{E.Evaluate{body,environment,frames}} : Result<S.Error,E.State>}

law bind_keeps_caller_scope:
  for +level: U32
  for +value: E.Value
  for +body: C.Term
  for +environment: List<&2,E.Entry>
  for +frames: List<&2,E.Frame>
  for book: C.Book
  {E.step(E.Return{value,Con{E.Bind{level,body,environment},frames}},book) == Done{E.Evaluate{body,Con{E.Entry{level,value},environment},frames}} : Result<S.Error,E.State>}

law unsigned_leb_boundary:
  {W.groups(5n,False{},128) == Done{[128,1]} : Result<S.Error,List<&2,U32>>}

law signed_leb_boundary:
  {W.groups(5n,True{},64) == Done{[192,0]} : Result<S.Error,List<&2,U32>>}

law unsigned_leb_maximum:
  {W.groups(5n,False{},4294967295) == Done{[255,255,255,255,15]} : Result<S.Error,List<&2,U32>>}

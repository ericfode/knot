import Base
import ./syntax.bend as S
import ./core.bend as C
import ./ownership.bend as O
import ./owned.bend as W
import ./heap-code.bend as A

law affine_occurrence_moves:
  for +future: List<&2,U32>
  for +level: U32
  {O.share(1,future,level) == False{} : Bool}

law reusable_last_occurrence_moves:
  for +level: U32
  {O.share(2,Nil{},level) == False{} : Bool}

law reusable_surviving_occurrence_shares:
  {O.share(2,[7],7) == True{} : Bool}

law erased_field_has_no_edge:
  for +token: S.Token
  for +type_id: U32
  for +rest: List<&2,C.Parameter>
  for +types: List<&2,C.Datatype>
  {O.edges(Con{C.Parameter{token,0,type_id},rest},types) == O.edges(rest,types) : List<&2,Bool>}

law erased_parameter_has_no_local:
  for +token: S.Token
  for +type_id: U32
  {O.parameters([C.Parameter{token,0,type_id}],0,0) == Nil{} : List<&2,O.Local>}

law live_local_preserves_level:
  for +token: S.Token
  for +type_id: U32
  {O.parameters([C.Parameter{token,0,type_id},C.Parameter{token,2,type_id}],0,0)
    == [O.Local{1,0,2,type_id}] : List<&2,O.Local>}

law empty_continuation_has_no_holders:
  for +index: U32
  for +quantity: U32
  for +type_id: U32
  {O.keep([O.Local{7,index,quantity,type_id}],Nil{}) == Nil{} : List<&2,O.Local>}

law surviving_continuation_keeps_holder:
  for +index: U32
  for +quantity: U32
  for +type_id: U32
  {O.keep([O.Local{7,index,quantity,type_id}],[7]) == [O.Local{7,index,quantity,type_id}] : List<&2,O.Local>}

law erased_initializer_has_no_use:
  for +token: S.Token
  for +type_id: U32
  {O.needs(4n,O.Term{C.Let{token,1,0,type_id,C.Reference{token,7,type_id},C.Value{token,type_id,0}}},Nil{})
    == Done{Nil{}} : Result<S.Error,List<&2,U32>>}

law branch_field_is_not_an_incoming_holder:
  for +token: S.Token
  for +type_id: U32
  {O.needs(4n,O.Arms{[C.Branch{0,[C.Binding{token,7,1,type_id,True{},None{}}],C.Reference{token,7,type_id}}]},Nil{})
    == Done{Nil{}} : Result<S.Error,List<&2,U32>>}

law wide_tail_uses_ordinary_call:
  for +index: U32
  {W.tail_calls([A.Index{18,index}],False{}) == [A.call(index)] : List<&2,A.Instruction>}

law narrow_tail_keeps_return_call:
  for +index: U32
  {W.tail_calls([A.Index{18,index}],True{}) == [A.Index{18,index}] : List<&2,A.Instruction>}

law ordinary_call_keeps_its_target:
  for +index: U32
  {W.tail_calls([A.call(index)],False{}) == [A.call(index)] : List<&2,A.Instruction>}

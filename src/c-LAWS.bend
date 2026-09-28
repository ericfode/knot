import Base
import ./syntax.bend as S
import ./core.bend as C
import ./c.bend as E

law erased_constructor_has_a_cell:
  for token: S.Token
  for name: S.Token
  for type_id: U32
  for rest: List<&2,C.Constructor>
  {E.fielded(Con{C.Constructor{token,[C.Parameter{name,0,type_id}]},rest}) == True{} : Bool}

law saved_calls_keep_their_continuation:
  for name: String
  for context: E.Context
  for index: U32
  {E.tail_call(E.Save{name},context,index) == False{} : Bool}

law erased_argument_has_no_code_or_slot:
  for +n: Nat
  for head: C.Term
  for +tail: List<&2,C.Term>
  for token: S.Token
  for type_id: U32
  for +params: List<&2,C.Parameter>
  for +slots: List<&2,E.Slot>
  for +action: E.Action
  for +context: E.Context
  for +locals: List<&2,E.Local>
  for +next: U32
  for +cap: U32
  {E.lower(1n+n,E.Arguments{Con{head,tail},Con{C.Parameter{token,0,type_id},params},slots,action},context,locals,next,cap) == E.lower(n,E.Arguments{tail,params,slots,action},context,locals,next,cap) : Result<S.Error,E.Code>}

law erased_binding_has_no_initializer:
  for +n: Nat
  for token: S.Token
  for level: U32
  for type_id: U32
  for value: C.Term
  for +body: C.Term
  for +destination: E.Destination
  for +context: E.Context
  for +locals: List<&2,E.Local>
  for +next: U32
  for +cap: U32
  {E.lower(1n+n,E.Expression{C.Let{token,level,0,type_id,value,body},destination},context,locals,next,cap) == E.lower(n,E.Expression{body,destination},context,locals,next,cap) : Result<S.Error,E.Code>}

law erased_pattern_preserves_offset:
  for +n: Nat
  for token: S.Token
  for level: U32
  for type_id: U32
  for parameter: Bool
  for known: Maybe<&2,C.Term>
  for +tail: List<&2,C.Binding>
  for +pointer: String
  for +offset: U32
  for +body: C.Term
  for +destination: E.Destination
  for +context: E.Context
  for +locals: List<&2,E.Local>
  for +next: U32
  for +cap: U32
  {E.lower(1n+n,E.Unpack{Con{C.Binding{token,level,0,type_id,parameter,known},tail},pointer,offset,body,destination},context,locals,next,cap) == E.lower(n,E.Unpack{tail,pointer,offset,body,destination},context,locals,next,cap) : Result<S.Error,E.Code>}

law erased_parameter_preserves_saved_arguments:
  for token: S.Token
  for type_id: U32
  for +tail: List<&2,C.Parameter>
  for +slots: List<&2,E.Slot>
  for +level: U32
  {E.rebind(Con{C.Parameter{token,0,type_id},tail},slots,level) == E.rebind(tail,slots,U32.add(level,1)) : Result<S.Error,String>}

law two_parameters_rebind_before_loop:
  for +token: S.Token
  for +type_id: U32
  {E.rebind([C.Parameter{token,1,type_id},C.Parameter{token,1,type_id}],[E.Slot{"v0",type_id},E.Slot{"v1",type_id}],0) == Done{"p0 = v0;\np1 = v1;\ngoto knot_tail;\n"} : Result<S.Error,String>}

law zero_depth_is_exhausted:
  for mode: E.Mode
  for context: E.Context
  for locals: List<&2,E.Local>
  for next: U32
  for cap: U32
  {E.lower(0n,mode,context,locals,next,cap) == Fail{S.Exhausted{"emit",S.At{0,0,0,0}}} : Result<S.Error,E.Code>}

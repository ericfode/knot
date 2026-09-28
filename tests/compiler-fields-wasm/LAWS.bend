import Base
import ../../src/syntax.bend as S
import ../../src/core.bend as C
import ../../src/check.bend as K
import ../../src/wasm.bend as W

law enum_capability_preserved:
  for +types: List<&2,C.Datatype>
  {W.capability(W.Enum{},types) == K.enum_profile(types) : Result<S.Error,Unit>}

law fields_capability_follows_checking:
  for types: List<&2,C.Datatype>
  {W.capability(W.Fields{},types) == Done{Unit{}} : Result<S.Error,Unit>}

law erased_constructor_still_has_a_cell:
  for token: S.Token
  for name: S.Token
  for type_id: U32
  for rest: List<&2,C.Constructor>
  {W.fielded(Con{C.Constructor{token,[C.Parameter{name,0,type_id}]},rest}) == True{} : Bool}

law erased_argument_takes_no_slot:
  for +n: Nat
  for head: C.Term
  for +tail: List<&2,C.Term>
  for token: S.Token
  for type_id: U32
  for +params: List<&2,C.Parameter>
  for +slots: List<&2,U32>
  for +tag: U32
  for +heap: List<&2,U32>
  for +functions: List<&2,C.Function>
  for +locals: List<&2,W.Local>
  for +next: U32
  for +cap: U32
  {W.lower(1n+n,W.Cell{Con{head,tail},Con{C.Parameter{token,0,type_id},params},slots,tag},heap,functions,locals,next,cap) == W.lower(n,W.Cell{tail,params,slots,tag},heap,functions,locals,next,cap) : Result<S.Error,W.Code>}

law erased_pattern_keeps_offset_and_locals:
  for +n: Nat
  for token: S.Token
  for level: U32
  for type_id: U32
  for parameter: Bool
  for known: Maybe<&2,C.Term>
  for +tail: List<&2,C.Binding>
  for +pointer: U32
  for +offset: U32
  for +body: C.Term
  for +heap: List<&2,U32>
  for +functions: List<&2,C.Function>
  for +locals: List<&2,W.Local>
  for +next: U32
  for +cap: U32
  {W.lower(1n+n,W.Unpack{Con{C.Binding{token,level,0,type_id,parameter,known},tail},pointer,offset,body},heap,functions,locals,next,cap) == W.lower(n,W.Unpack{tail,pointer,offset,body},heap,functions,locals,next,cap) : Result<S.Error,W.Code>}

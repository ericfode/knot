import Base
import ../../../src/syntax.bend as S
import ../../../src/core.bend as C
import ../../../src/catalog.bend as G
import ../../../src/check.bend as K
import ../../../src/scope.bend as E

# Helper laws and literal parser witnesses, not a checker soundness theorem.
law empty_scope_uses_catalog:
  for types: List<&2,C.Datatype>
  for name: S.Token
  {G.scoped_type(types,name,Nil{}) == G.find_type(types,name,0) : Result<S.Error,G.TypeRef>}

law value_shadows_type:
  for types: List<&2,C.Datatype>
  for tail: List<&2,S.Token>
  for +loc: S.At
  {G.scoped_type(types,S.Token{"Flag",loc},Con{S.Token{"Flag",loc},tail})
   == Fail{S.Invalid{"check","type-shadow",loc}} : Result<S.Error,G.TypeRef>}

law function_reference_is_unsupported:
  for params: List<&2,C.Parameter>
  for result: U32
  for tail: List<&2,C.Signature>
  for +loc: S.At
  {K.global_variable(Con{C.Signature{S.Token{"f",loc},params,result},tail},S.Token{"f",loc})
   == Fail{S.Unsupported{"check","function-reference",loc}} : Result<S.Error,C.Binding>}

law local_value_precedes_function:
  for +tail: List<&2,C.Binding>
  for sigs: List<&2,C.Signature>
  for +loc: S.At
  {K.lookup(E.Scope{Con{C.Binding{S.Token{"f",loc},0,1,0,False{},None{}},tail},1,Nil{},True{},Nil{}},sigs,S.Token{"f",loc})
   == Done{C.Binding{S.Token{"f",loc},0,1,0,False{},None{}}} : Result<S.Error,C.Binding>}

law dotted_name_witness:
  {S.dotted("Flag.value") == True{} : Bool}

law simple_name_witness:
  {S.dotted("value") == False{} : Bool}

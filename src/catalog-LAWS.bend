import Base
import ./syntax.bend as S
import ./core.bend as C
import ./catalog.bend as G
import ./check.bend as K

# Auxiliary kind helper laws; public catalog refinement is tested separately.
law erased_field_has_no_kind_obligation:
  for data: Bool
  for child: Bool
  {G.field_kind(data,0,child) == True{} : Bool}

law data_live_field_requires_data:
  {G.field_kind(True{},1,False{}) == False{} : Bool}

law reusable_field_requires_data:
  for data: Bool
  {G.field_kind(data,2,False{}) == False{} : Bool}

law data_field_preserves_metadata:
  for +token: S.Token
  for +index: U32
  for data: Bool
  for name: S.Token
  for ctors: List<&2,C.Constructor>
  {G.field_type(token,2,data,G.TypeRef{index,C.Datatype{name,True{},ctors}}) == Done{C.Parameter{token,2,index}} : Result<S.Error,C.Parameter>}

law field_capability_is_not_acceptance:
  for +token: S.Token
  for head: C.Parameter
  for tail: List<&2,C.Parameter>
  for rest: List<&2,C.Constructor>
  {K.enum_constructors(Con{C.Constructor{token,Con{head,tail}},rest}) == Fail{S.Unsupported{"check","constructor-fields",S.at(token)}} : Result<S.Error,Unit>}

# An empty datatype is a valid catalog entry; no source value inhabits it.
law empty_datatype:
  for +name: S.Token
  for +data: Bool
  {G.datatype(Nil{},name,data) == Done{C.Datatype{name,data,Nil{}}} : Result<S.Error,C.Datatype>}

# `+` names no datatype declared before it; a bare binder may, and a name that is
# no earlier datatype promotes. A binder hides a datatype of its name from later types.
def word(+offset: U32) -> S.Token: S.Token{"Flag",S.At{offset,offset,1,0}}
def flag() -> C.Datatype: C.Datatype{word(10),True{},Nil{}}
def rejected() -> Result<S.Error,Unit>: Fail{S.Invalid{"check","datatype-pattern-binder",S.At{20,20,1,0}}}

law promoted_datatype_is_rejected:
  {G.promotion([flag()],word(20),True{}) == rejected() : Result<S.Error,Unit>}

law bare_datatype_name_binds:
  {G.promotion([flag()],word(20),False{}) == Done{Unit{}} : Result<S.Error,Unit>}

law later_datatype_is_no_datatype:
  {G.promotion([flag()],word(5),True{}) == Done{Unit{}} : Result<S.Error,Unit>}

law hidden_type_is_rejected:
  {G.hidden(Unit,[word(1)],word(20),u => Done{Unit{}}) == Fail{S.Invalid{"check","type-shadowed",S.At{20,20,1,0}}} : Result<S.Error,Unit>}

law unrelated_binder_hides_nothing:
  {G.hidden(Unit,[S.Token{"x",S.At{1,1,1,0}}],word(20),u => Done{Unit{}}) == Done{Unit{}} : Result<S.Error,Unit>}

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

# The seed reads a type as a term: a binder shadows the type of its name in each
# later type position of its scope (fields, parameters, result), never its own.
law type_positions_read_their_scope:
  for +at: S.At
  for +here: S.At
  for +ctors: List<&2,C.Constructor>
  for +body: S.Node
  {(G.fields([S.Parameter{S.Token{"Light",at},1,S.Token{"Light",at}}],[C.Datatype{S.Token{"Light",at},False{},ctors}],False{},Nil{},0),
    G.fields([S.Parameter{S.Token{"Light",at},1,S.Token{"Light",at}},S.Parameter{S.Token{"v",at},1,S.Token{"Light",here}}],
      [C.Datatype{S.Token{"Light",at},False{},ctors}],False{},Nil{},0),
    G.collect_signatures([S.Function{S.Token{"f",at},[S.Parameter{S.Token{"Light",at},1,S.Token{"Light",at}},
      S.Parameter{S.Token{"x",at},1,S.Token{"Light",here}}],S.Token{"Light",at},body}],[C.Datatype{S.Token{"Light",at},False{},ctors}],0),
    G.collect_signatures([S.Function{S.Token{"f",at},[S.Parameter{S.Token{"Light",at},1,S.Token{"Light",at}}],S.Token{"Light",here},body}],
      [C.Datatype{S.Token{"Light",at},False{},ctors}],0))
   == (Done{[C.Parameter{S.Token{"Light",at},1,0}]},Fail{S.Invalid{"check","binder-as-type",here}},
       Fail{S.Invalid{"check","binder-as-type",here}},Fail{S.Invalid{"check","binder-as-type",here}})
   : Result<S.Error,List<&2,C.Parameter>> & Result<S.Error,List<&2,C.Parameter>>
     & Result<S.Error,List<&2,C.Signature>> & Result<S.Error,List<&2,C.Signature>>}

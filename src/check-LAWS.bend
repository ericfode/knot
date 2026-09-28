import Base
import ./syntax.bend as S
import ./core.bend as C
import ./scope.bend as E
import ./check.bend as K

# These are helper/boundary laws. They are not a checker soundness theorem.
law empty_sequence_preserves_uses:
  for +uses: List<&2,U32>
  for token: S.Token
  {E.sequential(Nil{},uses,token)
   == Done{uses}
   : Result<S.Error,List<&2,U32>>}

law repeated_affine_level:
  for +token: S.Token
  {E.sequential([0],[0],token)
   == Fail{S.Invalid{"check","affine-reuse",S.at(token)}}
   : Result<S.Error,List<&2,U32>>}

law live_erased_occurrence:
  for +token: S.Token
  for level: U32
  for type_id: U32
  {E.occurrence(None{},token,level,0,type_id,True{})
   == Fail{S.Invalid{"check","erased-live",S.at(token)}}
   : Result<S.Error,C.Checked>}

law erased_occurrence_preserves_identity:
  for token: S.Token
  for level: U32
  for type_id: U32
  {E.occurrence(None{},token,level,0,type_id,False{})
   == Done{C.Checked{C.Reference{token,level,type_id},type_id,Nil{}}}
   : Result<S.Error,C.Checked>}

law refined_constructor_is_fresh:
  for token: S.Token
  for type_id: U32
  for tag: U32
  {E.occurrence(Some{C.Value{token,type_id,tag}},token,0,1,type_id,True{})
   == Done{C.Checked{C.Value{token,type_id,tag},type_id,Nil{}}}
   : Result<S.Error,C.Checked>}

law nearest_binding_wins:
  for +tail: List<&2,C.Binding>
  for +level: U32
  {E.find(Con{C.Binding{S.Token{"x",S.At{0,1,1,0}},level,1,0,True{},None{}},tail},S.Token{"x",S.At{7,8,2,0}}) == Done{C.Binding{S.Token{"x",S.At{0,1,1,0}},level,1,0,True{},None{}}} : Result<S.Error,C.Binding>}

law no_checker_budget:
  for node: S.Node
  {K.check(0n,node) == Fail{S.Exhausted{"check",S.At{0,0,0,0}}} : Result<S.Error,C.Book>}

law file_let_meets_only_earlier_constructors:
  for +at: S.At
  for value: S.Node
  for body: S.Node
  {(K.rebinds(8n,[S.Datatype{S.Token{"Flag",at},False{},[S.Constructor{S.Token{"Off",at},Nil{}}]},
      S.Function{S.Token{"f",at},Nil{},S.Token{"Flag",at},S.Binding{S.Token{"Off",at},1,None{},value,body}}],Nil{}),
    K.rebinds(8n,[S.Function{S.Token{"f",at},Nil{},S.Token{"Flag",at},
        S.Binding{S.Token{"Off",at},1,None{},S.Variable{S.Token{"x",at}},S.Variable{S.Token{"Off",at}}}},
      S.Datatype{S.Token{"Flag",at},False{},[S.Constructor{S.Token{"Off",at},Nil{}}]}],Nil{}))
   == (Fail{S.Invalid{"check","constructor-pattern-binder",at}},Done{Unit{}})
   : Result<S.Error,Unit> & Result<S.Error,Unit>}

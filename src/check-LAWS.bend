import Base
import ./syntax.bend as S
import ./core.bend as C
import ./scope.bend as E
import ./check.bend as K
import ./literal-check.bend as L
import ./literal-matrix.bend as M

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

law dead_arm_invalid:
  for +phase: String
  for code: String
  for +at: S.At
  {K.dead_arm(Fail{S.Invalid{phase,code,at}}) == Fail{S.Unsupported{phase,"dead-arm",at}} : Result<S.Error,C.Checked>}

law dead_arm_exhausted:
  for +phase: String
  for +at: S.At
  {K.dead_arm(Fail{S.Exhausted{phase,at}}) == Fail{S.Exhausted{phase,at}} : Result<S.Error,C.Checked>}

# L.primitive_type's cases: the installed primitive wins; without it, the
# target decides by the constructor the literal spells (M.literal).
law installed_literal_type:
  for +token: S.Token
  for target: Maybe<&2,U32>
  for spelling: S.Node
  {L.primitive_type([C.Datatype{S.Token{"Nat",S.At{0,0,0,0}},True{},Nil{}}],1,token,target,spelling) == Done{0} : Result<S.Error,U32>}

law spelled_own_literal:
  for +token: S.Token
  for +fields: List<&2,C.Parameter>
  {L.primitive_type([C.Datatype{S.Token{"N",S.At{5,6,1,5}},True{},[C.Constructor{S.Token{"Zero",S.At{19,23,2,2}},Nil{}},C.Constructor{S.Token{"Succ",S.At{28,32,3,2}},fields}]}],
     1,token,Some{0},M.literal(S.Literal{token,1,2,Nil{}}))
   == Fail{S.Unsupported{"check","literal-base-type",S.at(token)}} : Result<S.Error,U32>}

law unspelled_literal:
  for +token: S.Token
  for +fields: List<&2,C.Parameter>
  {L.primitive_type([C.Datatype{S.Token{"N",S.At{5,6,1,5}},True{},[C.Constructor{S.Token{"Z",S.At{19,20,2,2}},Nil{}},C.Constructor{S.Token{"S",S.At{25,26,3,2}},fields}]}],
     1,token,Some{0},M.literal(S.Literal{token,1,0,Nil{}}))
   == Fail{S.Invalid{"check","unknown-type",S.at(token)}} : Result<S.Error,U32>}

law word_spells_any_target:
  for +token: S.Token
  for +number: U32
  for +ctors: List<&2,C.Constructor>
  {L.primitive_type([C.Datatype{S.Token{"Answer",S.At{5,11,1,5}},False{},ctors}],0,token,Some{0},M.literal(S.Literal{token,0,number,Nil{}}))
   == Fail{S.Unsupported{"check","literal-base-type",S.at(token)}} : Result<S.Error,U32>}

law untargeted_literal:
  for +token: S.Token
  for spelling: S.Node
  {L.primitive_type(Nil{},3,token,None{},spelling) == Fail{S.Invalid{"check","unknown-type",S.at(token)}} : Result<S.Error,U32>}

# An offset expression checks as its matrix spelling (M.literal): `2n+Zero{}`
# is two Succ constructors around the checked tail, in any scope.
law offset_spelling:
  for +token: S.Token
  for current: U32
  for scope: E.Scope
  {K.run(16n,K.Expression{S.Offset{token,2,S.Constructor{S.Token{"Zero",S.At{0,0,0,0}},Nil{}}},Some{0}},
     C.Catalog{[C.Datatype{S.Token{"Nat",S.At{0,0,0,0}},True{},[C.Constructor{S.Token{"Zero",S.At{0,0,0,0}},Nil{}},
       C.Constructor{S.Token{"Succ",S.At{0,0,0,0}},[C.Parameter{S.Token{"pred",S.At{0,0,0,0}},1,0}]}]}],Nil{}},current,scope)
   == Done{C.Checked{C.Construct{M.retoken("Succ",token),0,1,[C.Parameter{S.Token{"pred",S.At{0,0,0,0}},1,0}],
        [C.Construct{M.retoken("Succ",token),0,1,[C.Parameter{S.Token{"pred",S.At{0,0,0,0}},1,0}],
          [C.Value{S.Token{"Zero",S.At{0,0,0,0}},0,0}]}]},0,Nil{}}} : Result<S.Error,C.Checked>}

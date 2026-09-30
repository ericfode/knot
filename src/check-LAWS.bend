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

# A let without an annotation infers its value, and inference has no type for a
# constructor term: a binder refined to a constructor elaborates to one, as a
# literal does. An annotation, or a term that is not a constructor, stands.
law refined_value_needs_annotation:
  for +token: S.Token
  for +uses: List<&2,U32>
  for +type_id: U32
  for tag: U32
  {K.expected(token,None{},C.Checked{C.Value{token,type_id,tag},type_id,uses})
   == Fail{S.Invalid{"check","annotation-required",S.at(token)}}
   : Result<S.Error,C.Checked>}

law refined_construct_needs_annotation:
  for +token: S.Token
  for +fields: List<&2,C.Parameter>
  for +args: List<&2,C.Term>
  for +uses: List<&2,U32>
  for +type_id: U32
  for tag: U32
  {K.expected(token,None{},C.Checked{C.Construct{token,type_id,tag,fields,args},type_id,uses})
   == Fail{S.Invalid{"check","annotation-required",S.at(token)}}
   : Result<S.Error,C.Checked>}

law unrefined_binder_is_inferable:
  for +token: S.Token
  for +uses: List<&2,U32>
  for +level: U32
  for +type_id: U32
  {K.expected(token,None{},C.Checked{C.Reference{token,level,type_id},type_id,uses})
   == Done{C.Checked{C.Reference{token,level,type_id},type_id,uses}}
   : Result<S.Error,C.Checked>}

law annotation_admits_constructor:
  for +token: S.Token
  for tag: U32
  {K.expected(token,Some{0},C.Checked{C.Value{token,0,tag},0,Nil{}})
   == Done{C.Checked{C.Value{token,0,tag},0,Nil{}}}
   : Result<S.Error,C.Checked>}

law nearest_binding_wins:
  for +tail: List<&2,C.Binding>
  for +level: U32
  {E.find(Con{C.Binding{S.Token{"x",S.At{0,1,1,0}},level,1,0,True{},None{}},tail},S.Token{"x",S.At{7,8,2,0}}) == Done{C.Binding{S.Token{"x",S.At{0,1,1,0}},level,1,0,True{},None{}}} : Result<S.Error,C.Binding>}

law no_checker_budget:
  for node: S.Node
  {K.check(0n,node) == Fail{S.Exhausted{"check",S.At{0,0,0,0}}} : Result<S.Error,C.Book>}

# An unbound dotted binder is a reference to the seed; a bound one rebinds.
law dotted_binder_rebinds_only_a_bound_name:
  for +at: S.At
  {(E.binder(Nil{},S.Token{"a.b",at}),
    E.binder([C.Binding{S.Token{"a.b",at},0,1,0,True{},None{}}],S.Token{"a.b",at}),
    E.binder(Nil{},S.Token{"ab",at}))
   == (Fail{S.Invalid{"check","dotted-binder",at}},Done{Unit{}},Done{Unit{}})
   : Result<S.Error,Unit> & Result<S.Error,Unit> & Result<S.Error,Unit>}

# A let annotation reads the scope: a binder shadows the type of its name.
law annotation_reads_the_scope:
  for +at: S.At
  for +here: S.At
  for +ctors: List<&2,C.Constructor>
  {(K.annotation([C.Datatype{S.Token{"Light",at},False{},ctors}],Nil{},Some{S.Token{"Light",at}}),
    K.annotation([C.Datatype{S.Token{"Light",at},False{},ctors}],[C.Binding{S.Token{"Light",at},0,1,0,True{},None{}}],
      Some{S.Token{"Light",here}}))
   == (Done{Some{0}},Fail{S.Invalid{"check","binder-as-type",here}})
   : Result<S.Error,Maybe<&2,U32>> & Result<S.Error,Maybe<&2,U32>>}

# A term name resolves lexically first. Unbound, a type or function is a value
# Knot cannot represent yet; a constructor without braces is not a term.
law term_names_a_binder_or_a_declaration:
  for +at: S.At
  for +params: List<&2,C.Parameter>
  {(E.term(E.Scope{[C.Binding{S.Token{"flip",at},0,1,0,True{},None{}}],1,Nil{},True{},Nil{}},
      C.Catalog{[C.Datatype{S.Token{"Light",at},False{},[C.Constructor{S.Token{"Lit",at},Nil{}}]}],[C.Signature{S.Token{"flip",at},params,0}]},
      S.Token{"flip",at}),
    E.term(E.Scope{Nil{},0,Nil{},True{},Nil{}},
      C.Catalog{[C.Datatype{S.Token{"Light",at},False{},[C.Constructor{S.Token{"Lit",at},Nil{}}]}],[C.Signature{S.Token{"flip",at},params,0}]},
      S.Token{"Light",at}),
    E.term(E.Scope{Nil{},0,Nil{},True{},Nil{}},
      C.Catalog{[C.Datatype{S.Token{"Light",at},False{},[C.Constructor{S.Token{"Lit",at},Nil{}}]}],[C.Signature{S.Token{"flip",at},params,0}]},
      S.Token{"flip",at}),
    E.term(E.Scope{Nil{},0,Nil{},True{},Nil{}},
      C.Catalog{[C.Datatype{S.Token{"Light",at},False{},[C.Constructor{S.Token{"Lit",at},Nil{}}]}],[C.Signature{S.Token{"flip",at},params,0}]},
      S.Token{"Lit",at}))
   == (Done{C.Binding{S.Token{"flip",at},0,1,0,True{},None{}}},Fail{S.Unsupported{"check","type-as-term",at}},
       Fail{S.Unsupported{"check","function-reference",at}},Fail{S.Invalid{"check","free-name",at}})
   : Result<S.Error,C.Binding> & Result<S.Error,C.Binding> & Result<S.Error,C.Binding> & Result<S.Error,C.Binding>}
# The core budget is one unit per node, every copy of a shared default counted, and it stops when spent.
law weight_counts_every_node:
  for +token: S.Token
  {K.weight(9n,[C.Case{token,0,0,[C.Branch{0,Nil{},C.Value{token,0,0}},C.Branch{1,Nil{},C.Value{token,0,0}}]}],9)
   == 4
   : U32}

law weight_stops_when_spent:
  for +token: S.Token
  {K.weight(9n,[C.Case{token,0,0,[C.Branch{0,Nil{},C.Value{token,0,0}},C.Branch{1,Nil{},C.Value{token,0,0}}]}],4)
   == 0
   : U32}

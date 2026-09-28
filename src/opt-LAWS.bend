import Base
import ./syntax.bend as S
import ./core.bend as C
import ./opt-term.bend as T
import ./opt-fold.bend as F
import ./opt-inline.bend as I
import ./opt.bend as O

# These are local rewrite and composition equations. Corpus differentials
# establish their integration; they are not a general compiler refinement.
law matching_arm_is_selected:
  for +fields: List<&2,C.Binding>
  for +body: C.Term
  for other: C.Term
  for rest: List<&2,C.Term>
  {F.select(Con{C.Branch{0,Nil{},other},Con{C.Branch{1,fields,body},rest}},1) ==
    Done{C.Branch{1,fields,body}} : Result<S.Error,C.Term>}

law value_case_returns_matching_body:
  for token: S.Token
  for typ: U32
  for +body: C.Term
  for other: C.Term
  {F.constant(C.Value{token,typ,1},[C.Branch{0,Nil{},other},C.Branch{1,Nil{},body}]) ==
    Done{Some{body}} : Result<S.Error,Maybe<&2,C.Term>>}

law fields_bind_in_declaration_order:
  for +token: S.Token
  for +a: C.Term
  for +b: C.Term
  for +body: C.Term
  {F.bind_fields([C.Binding{token,3,1,0,True{},None{}},C.Binding{token,4,2,0,True{},None{}}],[a,b],body) ==
    Done{C.Let{token,3,1,0,a,C.Let{token,4,2,0,b,body}}} : Result<S.Error,C.Term>}

law empty_field_binding_is_identity:
  for +body: C.Term
  {F.bind_fields(Nil{},Nil{},body) == Done{body} : Result<S.Error,C.Term>}

law zero_parameter_binding_is_identity:
  for +body: C.Term
  for base: U32
  {I.arguments(Nil{},Nil{},base,body) == Done{body} : Result<S.Error,C.Term>}

law arguments_bind_once_in_order:
  for +token: S.Token
  for +a: C.Term
  for +b: C.Term
  for +body: C.Term
  {I.arguments([C.Parameter{token,1,0},C.Parameter{token,0,0}],[a,b],7,body) ==
    Done{C.Let{token,7,1,0,a,C.Let{token,8,0,0,b,body}}} : Result<S.Error,C.Term>}

law reference_translation:
  for +token: S.Token
  for +level: U32
  for +typ: U32
  for +offset: U32
  {T.shift(1n,C.Reference{token,level,typ},offset) ==
    Done{C.Reference{token,U32.add(level,offset),typ}} : Result<S.Error,C.Term>}

law dead_reusable_value_is_removed:
  for +token: S.Token
  for typ: U32
  for value: C.Term
  {F.dead(4n,token,3,2,typ,value,C.Value{token,0,1}) ==
    Done{C.Value{token,0,1}} : Result<S.Error,C.Term>}

law used_reusable_binding_is_retained:
  for +token: S.Token
  for +typ: U32
  for +value: C.Term
  {F.dead(4n,token,3,2,typ,value,C.Reference{token,3,typ}) ==
    Done{C.Let{token,3,2,typ,value,C.Reference{token,3,typ}}} : Result<S.Error,C.Term>}

# The function traversal rebuilds every export with this constructor; it never
# filters the list. This lemma is structural, not a quantified DCE theorem.
law export_reconstruction_preserves_signature:
  for +signature: C.Signature
  for +body: C.Term
  for +rest: List<&2,C.Function>
  {O.prepend(signature,body,rest) == Con{C.Function{signature,body},rest} : List<&2,C.Function>}

law empty_pipeline_is_identity:
  for depth: Nat
  for +book: C.Book
  {O.compose(Nil{},depth,book) == Done{book} : Result<S.Error,C.Book>}

law zero_pipeline_fuel_is_exhausted:
  for depth: Nat
  for book: C.Book
  {O.settle(0n,depth,book) == Fail{S.Exhausted{"opt",S.At{0,0,0,0}}} : Result<S.Error,C.Book>}

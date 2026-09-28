import Base
import ./syntax.bend as S
import ./core.bend as C
import ./eval.bend as E
import ./primitive-op.bend as O

law natural_literal:
  for token: S.Token
  for +id: U32
  for env: List<&2,E.Entry>
  for +frames: List<&2,E.Frame>
  {E.step(E.Evaluate{C.Literal{token,id,1,2,Nil{}},env,frames},C.Book{Nil{},Nil{}}) ==
    Done{E.Natural{id,2,E.Value{id,0},frames}} : Result<S.Error,E.State>}

law natural_cell:
  for +id: U32
  for +value: E.Value
  for +frames: List<&2,E.Frame>
  {E.step(E.Natural{id,1,value,frames},C.Book{Nil{},Nil{}}) ==
    Done{E.Natural{id,0,E.Object{id,1,[value]},frames}} : Result<S.Error,E.State>}

# `2n+t` checks as its matrix spelling Succ{Succ{t}}; that core builds the
# cells of a literal's Natural state around t's shared value instead of Zero.
law natural_offset:
  for +id: U32
  for +token: S.Token
  for +field: S.Token
  for tail: S.Token
  for +value: E.Value
  {E.run(9n,E.Evaluate{C.Construct{token,id,1,[C.Parameter{field,1,id}],
      [C.Construct{token,id,1,[C.Parameter{field,1,id}],[C.Reference{tail,0,id}]}]},[E.Entry{0,value}],Nil{}},C.Book{Nil{},Nil{}}) ==
    E.run(3n,E.Natural{id,2,value,Nil{}},C.Book{Nil{},Nil{}}) : Result<S.Error,E.Value>}

law intrinsic_arguments:
  for token: S.Token
  for +id: U32
  for +args: List<&2,C.Term>
  for +env: List<&2,E.Entry>
  for +frames: List<&2,E.Frame>
  {E.step(E.Evaluate{C.Intrinsic{token,id,O.WDiv{},args},env,frames},C.Book{Nil{},Nil{}}) ==
    Done{E.PrimitiveArguments{id,O.WDiv{},["U32","U32"],args,env,Nil{},frames}} : Result<S.Error,E.State>}

law default_selection:
  for +body: C.Term
  for tail: List<&2,C.Term>
  for tag: U32
  {E.select(Con{C.Default{body},tail},tag) == Done{C.Default{body}} : Result<S.Error,C.Term>}

law default_scope:
  for value: E.Value
  for +body: C.Term
  for +env: List<&2,E.Entry>
  for +frames: List<&2,E.Frame>
  {E.enter_branch(value,C.Default{body},env,frames) == Done{E.Evaluate{body,env,frames}} : Result<S.Error,E.State>}

law text_cell:
  for +id: U32
  for +char_id: U32
  for +code: U32
  for +tail: List<&2,U32>
  for +value: E.Value
  for +frames: List<&2,E.Frame>
  {E.step(E.TextBuild{id,char_id,Con{code,tail},value,frames},C.Book{Nil{},Nil{}}) ==
    Done{E.TextBuild{id,char_id,tail,E.Object{id,1,[E.Value{char_id,code},value]},frames}} : Result<S.Error,E.State>}

law primitive_fields_display_as_literals:
  {E.display(32n,E.One{E.Object{0,0,[E.Value{1,39},E.Value{2,300},E.Object{3,1,[E.Object{3,1,[E.Value{3,0}]}]},
      E.Object{4,1,[E.Value{1,97},E.Value{4,0}]}]}},
    [C.Datatype{S.Token{"Mix",S.At{0,3,1,5}},True{},[C.Constructor{S.Token{"Mix",S.At{0,3,2,2}},Nil{}}]},
     C.Datatype{S.Token{"Char",S.At{0,0,0,0}},True{},[C.Constructor{S.Token{"Chr",S.At{0,0,0,0}},Nil{}}]},
     C.Datatype{S.Token{"U32",S.At{0,0,0,0}},True{},[C.Constructor{S.Token{"#U32",S.At{0,0,0,0}},Nil{}}]},
     C.Datatype{S.Token{"Nat",S.At{0,0,0,0}},True{},[C.Constructor{S.Token{"Zero",S.At{0,0,0,0}},Nil{}}]},
     C.Datatype{S.Token{"String",S.At{0,0,0,0}},True{},[C.Constructor{S.Token{"SNil",S.At{0,0,0,0}},Nil{}}]}]) ==
    Done{"Mix{'\\'',300,2n,\"a\"}"} : Result<S.Error,String>}

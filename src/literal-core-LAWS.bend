import Base
import ./syntax.bend as S
import ./core.bend as C
import ./eval.bend as E
import ./primitive-op.bend as O
import ./literal-offset.bend as N

# Specification of the offset laws: k unary constructors around a value, and the
# transitions that build them. The compiler uses neither.
def cells(k: Nat, +id: U32, +tag: U32, value: E.Value) -> E.Value:
  match k:
    case 0n: value
    case 1n+p: E.Object{id,tag,[cells(p,id,tag,value)]}

def steps(k: Nat, c: Nat, m: Nat) -> Nat:
  match k:
    case 0n: Nat.add(c,m)
    case 1n+p: 1n+1n+steps(p,c,1n+1n+m)

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

# For every k and every tail term with a known value (ev: it returns v in c
# transitions under any frames and fuel, in any book), k successors around it
# return k cells around v in 4k+c transitions. Ground instance k=2, c=1:
# natural_offset.
law offset_cells:
  for k: Nat
  for +id: U32
  for +tag: U32
  for +token: S.Token
  for +field: S.Token
  for +term: C.Term
  for +env: List<&2,E.Entry>
  for +v: E.Value
  for +c: Nat
  for +book: C.Book
  for ev: @fr: List<&2,E.Frame> -> @m: Nat ->
    {E.run(m,E.Return{v,fr},book) == E.run(Nat.add(c,m),E.Evaluate{term,env,fr},book) : Result<S.Error,E.Value>}
  for m: Nat
  for +frames: List<&2,E.Frame>
  {E.run(m,E.Return{cells(k,id,tag,v),frames},book) ==
    E.run(steps(k,c,m),E.Evaluate{N.successors(k,term,token,id,tag,[C.Parameter{field,1,id}]),env,frames},book) : Result<S.Error,E.Value>}

# The hypothesis of offset_cells holds for a call: a tail that calls a book's
# constant function returns its value in 3 transitions, so 2 successors take 11.
law offset_cells_call:
  for +tok: S.Token
  {E.run(0n,E.Return{cells(2n,1,1,E.Value{1,0}),Nil{}},C.Book{Nil{},[C.Function{C.Signature{tok,Nil{},1},C.Value{tok,1,0}}]}) ==
    E.run(11n,E.Evaluate{N.successors(2n,C.Application{tok,0,1,Nil{}},tok,1,1,[C.Parameter{tok,1,1}]),Nil{},Nil{}},
      C.Book{Nil{},[C.Function{C.Signature{tok,Nil{},1},C.Value{tok,1,0}}]}) : Result<S.Error,E.Value>}

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

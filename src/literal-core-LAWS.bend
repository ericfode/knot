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

import Base
import ./syntax.bend as S
import ./core.bend as C
import ./scope.bend as E
import ./patterns.bend as P
import ./eval.bend as V

law erased_field_stays_erased:
  for parent: U32
  for mark: U32
  {P.quantity(0,parent,mark) == 0 : U32}

law affine_field_can_promote:
  {P.quantity(1,1,2) == 2 : U32}

law reusable_parent_shares_field:
  {P.quantity(1,2,1) == 2 : U32}

law frontier_retains_later_parameters:
  {E.after([4,7,1,2],7) == [1,2] : List<&2,U32>}

law erased_field_skips_evaluation:
  for +type_id: U32
  for +tag: U32
  for token: S.Token
  for typ: U32
  for +params: List<&2,C.Parameter>
  for head: C.Term
  for +args: List<&2,C.Term>
  for +env: List<&2,V.Entry>
  for +values: List<&2,V.Value>
  for +frames: List<&2,V.Frame>
  for book: C.Book
  {V.step(V.Fields{type_id,tag,Con{C.Parameter{token,0,typ},params},Con{head,args},env,values,frames},book) == Done{V.Fields{type_id,tag,params,args,env,values,frames}} : Result<S.Error,V.State>}

law erased_pattern_keeps_live_slots:
  for token: S.Token
  for level: U32
  for typ: U32
  for param: Bool
  for known: Maybe<&2,C.Term>
  for +params: List<&2,C.Binding>
  for +values: List<&2,V.Value>
  for +env: List<&2,V.Entry>
  for +body: C.Term
  for +frames: List<&2,V.Frame>
  for book: C.Book
  {V.step(V.Unpack{Con{C.Binding{token,level,0,typ,param,known},params},values,env,body,frames},book) == Done{V.Unpack{params,values,env,body,frames}} : Result<S.Error,V.State>}

law unpack_preserves_identity_and_tail:
  for +value: V.Value
  for +tail: List<&2,V.Value>
  for +level: U32
  for +params: List<&2,C.Binding>
  for +env: List<&2,V.Entry>
  for +body: C.Term
  for +frames: List<&2,V.Frame>
  {V.unpack_live(Con{value,tail},level,params,env,body,frames) == Done{V.Unpack{params,tail,Con{V.Entry{level,value},env},body,frames}} : Result<S.Error,V.State>}

law field_completion_preserves_declaration_order:
  for +type_id: U32
  for +tag: U32
  for +first: V.Value
  for +second: V.Value
  for env: List<&2,V.Entry>
  for +frames: List<&2,V.Frame>
  for book: C.Book
  {V.step(V.Fields{type_id,tag,Nil{},Nil{},env,[second,first],frames},book) == Done{V.Return{V.Object{type_id,tag,[first,second]},frames}} : Result<S.Error,V.State>}

law inspection_exhaustion_is_explicit:
  for mode: V.Display
  for types: List<&2,C.Datatype>
  {V.display(0n,mode,types) == Fail{S.Exhausted{"inspect",S.At{0,0,0,0}}} : Result<S.Error,String>}

law inspection_capacity_rejects_overflow:
  for types: List<&2,C.Datatype>
  {V.render(1n,[V.Text{"x"}],types,0n,Nil{}) == Fail{S.Exhausted{"inspect",S.At{0,0,0,0}}} : Result<S.Error,String>}

law inspection_capacity_accepts_exact_fit:
  for types: List<&2,C.Datatype>
  {V.render(1n,[V.Text{"x"}],types,1n,Nil{}) == Done{"x"} : Result<S.Error,String>}

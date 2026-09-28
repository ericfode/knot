import Base
import ./syntax.bend as S
import ./core.bend as C
import ./scope.bend as E
import ./patterns.bend as P
import ./check.bend as K
import ./eval.bend as V
import ./descent.bend as D

# Scope and call boundaries; these are not a general termination theorem.
def parameter(+token: S.Token, level: U32, known: Maybe<&2,C.Term>) -> C.Binding:
  C.Binding{token,level,1,0,True{},known}

def successor(+token: S.Token, level: U32) -> C.Term:
  C.Construct{token,0,1,[C.Parameter{token,1,0}],[C.Reference{token,level,0}]}

law local_binding_preserves_descent:
  for +bindings: List<&2,C.Binding>
  for +next: U32
  for open: List<&2,U32>
  for +live: Bool
  for +aliases: List<&2,D.Alias>
  for +token: S.Token
  for +q: U32
  for +type_id: U32
  for +value: C.Term
  {E.extend(E.Scope{bindings,next,open,live,aliases},token,q,type_id,value) ==
    E.Scope{Con{C.Binding{token,next,q,type_id,False{},None{}},bindings},U32.add(next,1),Nil{},live,Con{D.Alias{next,value},aliases}} : E.Scope}

law opening_root_records_descent:
  for +token: S.Token
  for +bindings: List<&2,C.Binding>
  for +params: List<&2,C.Parameter>
  for +args: List<&2,C.Term>
  for +aliases: List<&2,D.Alias>
  {P.finish(P.Fields{E.Scope{bindings,2,Nil{},True{},aliases},[C.Binding{token,1,1,0,True{},None{}}],args},token,0,0,0,params) ==
    P.Fields{E.Scope{E.replace(bindings,0,P.value(token,0,0,params,args)),2,[1],True{},aliases},[C.Binding{token,1,1,0,True{},None{}}],args} : P.Fields}

law opening_descendant_records_descent:
  for +token: S.Token
  for +bindings: List<&2,C.Binding>
  for +params: List<&2,C.Parameter>
  for +args: List<&2,C.Term>
  for +aliases: List<&2,D.Alias>
  {P.finish(P.Fields{E.Scope{bindings,3,Nil{},True{},aliases},[C.Binding{token,2,1,0,True{},None{}}],args},token,1,0,0,params) ==
    P.Fields{E.Scope{E.replace(bindings,1,P.value(token,0,0,params,args)),3,[2],True{},aliases},[C.Binding{token,2,1,0,True{},None{}}],args} : P.Fields}

law descending_self_call_is_checked:
  for +token: S.Token
  for +uses: List<&2,U32>
  {K.call_result(C.Checked{C.Sequence{[C.Reference{token,1,0}]},0,uses},token,0,0,0,
    E.Scope{[parameter(token,0,Some{successor(token,1)}),parameter(token,1,None{})],2,[1],True{},Nil{}},32n,[C.Parameter{token,1,0}]) ==
    Done{C.Checked{C.Application{token,0,0,[C.Reference{token,1,0}]},0,uses}} : Result<S.Error,C.Checked>}

law nondecreasing_self_call_is_invalid:
  for +token: S.Token
  for uses: List<&2,U32>
  {K.call_result(C.Checked{C.Sequence{[C.Reference{token,0,0}]},0,uses},token,0,0,0,
    E.Scope{[parameter(token,0,None{})],1,[0],True{},Nil{}},32n,[C.Parameter{token,1,0}]) ==
    Fail{S.Invalid{"check","recursive-call",S.at(token)}} : Result<S.Error,C.Checked>}

law rebuilt_parent_does_not_decrease:
  for +token: S.Token
  {K.call_result(C.Checked{C.Sequence{[successor(token,1)]},0,Nil{}},token,0,0,0,
    E.Scope{[parameter(token,0,Some{successor(token,1)}),parameter(token,1,None{})],2,[1],True{},Nil{}},32n,[C.Parameter{token,1,0}]) ==
    Fail{S.Invalid{"check","recursive-call",S.at(token)}} : Result<S.Error,C.Checked>}

law later_argument_establishes_descent:
  for +token: S.Token
  for +uses: List<&2,U32>
  {K.call_result(C.Checked{C.Sequence{[C.Reference{token,0,0},C.Reference{token,2,0}]},0,uses},token,0,0,0,
    E.Scope{[parameter(token,0,None{}),parameter(token,1,Some{successor(token,2)}),parameter(token,2,None{})],3,[2],True{},Nil{}},32n,
    [C.Parameter{token,1,0},C.Parameter{token,1,0}]) ==
    Done{C.Checked{C.Application{token,0,0,[C.Reference{token,0,0},C.Reference{token,2,0}]},0,uses}} : Result<S.Error,C.Checked>}

law earlier_growth_blocks_later_descent:
  for +token: S.Token
  {K.call_result(C.Checked{C.Sequence{[successor(token,0),C.Reference{token,2,0}]},0,Nil{}},token,0,0,0,
    E.Scope{[parameter(token,0,None{}),parameter(token,1,Some{successor(token,2)}),parameter(token,2,None{})],3,[2],True{},Nil{}},32n,
    [C.Parameter{token,1,0},C.Parameter{token,1,0}]) ==
    Fail{S.Invalid{"check","recursive-call",S.at(token)}} : Result<S.Error,C.Checked>}

law dead_self_call_needs_no_descent:
  for +token: S.Token
  for +type_id: U32
  for +args: List<&2,C.Term>
  for +uses: List<&2,U32>
  for bindings: List<&2,C.Binding>
  for aliases: List<&2,D.Alias>
  for params: List<&2,C.Parameter>
  {K.call_result(C.Checked{C.Sequence{args},0,uses},token,0,type_id,0,E.Scope{bindings,0,Nil{},False{},aliases},0n,params) ==
    Done{C.Checked{C.Application{token,0,type_id,args},type_id,uses}} : Result<S.Error,C.Checked>}

law earlier_call_needs_no_descent:
  for +token: S.Token
  for +type_id: U32
  for +args: List<&2,C.Term>
  for +uses: List<&2,U32>
  for scope: E.Scope
  for params: List<&2,C.Parameter>
  {K.call_result(C.Checked{C.Sequence{args},0,uses},token,0,type_id,1,scope,0n,params) ==
    Done{C.Checked{C.Application{token,0,type_id,args},type_id,uses}} : Result<S.Error,C.Checked>}

law recursive_evaluation_exhaustion:
  for token: S.Token
  for index: U32
  for type_id: U32
  for args: List<&2,C.Term>
  for env: List<&2,V.Entry>
  for frames: List<&2,V.Frame>
  for book: C.Book
  {V.run(0n,V.Evaluate{C.Application{token,index,type_id,args},env,frames},book) ==
    Fail{S.Exhausted{"eval",S.At{0,0,0,0}}} : Result<S.Error,V.Value>}

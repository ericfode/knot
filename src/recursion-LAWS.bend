import Base
import ./syntax.bend as S
import ./core.bend as C
import ./scope.bend as E
import ./patterns.bend as P
import ./check.bend as K
import ./eval.bend as V

# Scope and call boundaries; these are not a general termination theorem.
law root_fields_are_smaller:
  for +fields: List<&2,U32>
  for +smaller: List<&2,U32>
  {E.descendants(0,fields,smaller) == List.append(&2,U32,fields,smaller) : List<&2,U32>}

law descendant_fields_are_smaller:
  for +fields: List<&2,U32>
  {E.descendants(2,fields,[2,1]) == List.append(&2,U32,fields,[2,1]) : List<&2,U32>}

law unrelated_fields_stay_unmarked:
  for fields: List<&2,U32>
  {E.descendants(3,fields,[2,1]) == [2,1] : List<&2,U32>}

law marked_reference_descends:
  for token: S.Token
  for type_id: U32
  for tail: List<&2,C.Term>
  {E.descends(Con{C.Reference{token,2,type_id},tail},[2,1]) == True{} : Bool}

law root_reference_does_not_descend:
  for token: S.Token
  for type_id: U32
  for tail: List<&2,C.Term>
  {E.descends(Con{C.Reference{token,0,type_id},tail},[2,1]) == False{} : Bool}

law rebuilt_argument_does_not_descend:
  for token: S.Token
  for type_id: U32
  for tag: U32
  for params: List<&2,C.Parameter>
  for args: List<&2,C.Term>
  for smaller: List<&2,U32>
  {E.descends([C.Construct{token,type_id,tag,params,args}],smaller) == False{} : Bool}

law computed_argument_does_not_descend:
  for token: S.Token
  for index: U32
  for type_id: U32
  for args: List<&2,C.Term>
  for smaller: List<&2,U32>
  {E.descends([C.Application{token,index,type_id,args}],smaller) == False{} : Bool}

law empty_call_does_not_descend:
  for smaller: List<&2,U32>
  {E.descends(Nil{},smaller) == False{} : Bool}

law later_argument_cannot_establish_descent:
  for +token: S.Token
  for +type_id: U32
  {E.descends([C.Reference{token,0,type_id},C.Reference{token,1,type_id}],[1]) == False{} : Bool}

law local_binding_preserves_descent:
  for +bindings: List<&2,C.Binding>
  for +next: U32
  for open: List<&2,U32>
  for +live: Bool
  for +smaller: List<&2,U32>
  for +token: S.Token
  for +q: U32
  for +type_id: U32
  {E.extend(E.Scope{bindings,next,open,live,smaller},token,q,type_id) ==
    E.Scope{Con{C.Binding{token,next,q,type_id,False{},None{}},bindings},U32.add(next,1),Nil{},live,smaller} : E.Scope}

law opening_root_records_descent:
  for +token: S.Token
  for +bindings: List<&2,C.Binding>
  for +params: List<&2,C.Parameter>
  for +args: List<&2,C.Term>
  {P.finish(P.Fields{E.Scope{bindings,2,Nil{},True{},Nil{}},[C.Binding{token,1,1,0,True{},None{}}],args},token,0,0,0,params) ==
    P.Fields{E.Scope{E.replace(bindings,0,P.value(token,0,0,params,args)),2,[1],True{},[1]},[C.Binding{token,1,1,0,True{},None{}}],args} : P.Fields}

law opening_descendant_records_descent:
  for +token: S.Token
  for +bindings: List<&2,C.Binding>
  for +params: List<&2,C.Parameter>
  for +args: List<&2,C.Term>
  {P.finish(P.Fields{E.Scope{bindings,3,Nil{},True{},[1]},[C.Binding{token,2,1,0,True{},None{}}],args},token,1,0,0,params) ==
    P.Fields{E.Scope{E.replace(bindings,1,P.value(token,0,0,params,args)),3,[2],True{},[2,1]},[C.Binding{token,2,1,0,True{},None{}}],args} : P.Fields}

law descending_self_call_is_checked:
  for +token: S.Token
  for +type_id: U32
  for +uses: List<&2,U32>
  for bindings: List<&2,C.Binding>
  {K.call_result(C.Checked{C.Sequence{[C.Reference{token,1,type_id}]},0,uses},token,0,type_id,0,E.Scope{bindings,2,[1],True{},[1]}) ==
    Done{C.Checked{C.Application{token,0,type_id,[C.Reference{token,1,type_id}]},type_id,uses}} : Result<S.Error,C.Checked>}

law nondecreasing_self_call_is_unsupported:
  for +token: S.Token
  for type_id: U32
  for uses: List<&2,U32>
  for bindings: List<&2,C.Binding>
  for live: Bool
  {K.call_result(C.Checked{C.Sequence{[C.Reference{token,0,type_id}]},0,uses},token,0,type_id,0,E.Scope{bindings,2,[1],live,[1]}) ==
    Fail{S.Unsupported{"check","recursive-call",S.at(token)}} : Result<S.Error,C.Checked>}

law earlier_call_needs_no_descent:
  for +token: S.Token
  for +type_id: U32
  for +args: List<&2,C.Term>
  for +uses: List<&2,U32>
  for scope: E.Scope
  {K.call_result(C.Checked{C.Sequence{args},0,uses},token,0,type_id,1,scope) ==
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

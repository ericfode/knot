import Base
import ./syntax.bend as S
import ./core.bend as C
import ./scope.bend as E
import ./closure-check.bend as H
import ./eval.bend as V

law discard_is_not_a_reference:
  for +at: S.At
  for bindings: List<&2,C.Binding>
  for level: U32
  for open: List<&2,U32>
  for live: Bool
  for smaller: List<&2,U32>
  {E.lookup(E.Scope{bindings,level,open,live,smaller},S.Token{"_",at}) ==
    Fail{S.Invalid{"check","free-name",at}} : Result<S.Error,C.Binding>}

law closure_application_is_a_computed_scrutinee:
  for +token: S.Token
  for function: S.Node
  for args: List<&2,S.Node>
  for scope: E.Scope
  {E.scrutinee(S.Apply{token,function,args},scope) ==
    Fail{S.Invalid{"check","computed-scrutinee",S.at(token)}} : Result<S.Error,C.Binding>}

law lambda_is_a_computed_scrutinee:
  for +token: S.Token
  for quantity: U32
  for body: S.Node
  for scope: E.Scope
  {E.scrutinee(S.Lambda{token,quantity,body},scope) ==
    Fail{S.Invalid{"check","computed-scrutinee",S.at(token)}} : Result<S.Error,C.Binding>}

law affine_capture_is_transferred:
  for +token: S.Token
  for +typ: U32
  for +domain: U32
  for +site: U32
  for sigs: List<&2,C.Signature>
  {H.close(C.Checked{C.Reference{token,3,domain},domain,[3]},token,site,typ,9,1,domain,
    [C.Binding{token,3,1,domain,True{},None{}}],sigs,1n) ==
    Done{C.Checked{C.Closure{token,site,typ,9,1,domain,[C.Binding{token,3,1,domain,False{},None{}}],C.Reference{token,3,domain}},typ,[3]}} : Result<S.Error,C.Checked>}

law affine_capture_cannot_be_consumed_twice:
  for +token: S.Token
  for function: C.Term
  for argument: C.Term
  for arrow: U32
  for domain: U32
  for result: U32
  {H.invoke(C.Checked{function,arrow,[3]},C.Checked{argument,domain,[3]},token,result) ==
    Fail{S.Invalid{"check","affine-reuse",S.at(token)}} : Result<S.Error,C.Checked>}

law erased_argument_has_no_live_read:
  for +token: S.Token
  for typ: U32
  for sigs: List<&2,C.Signature>
  {H.scan(3n,H.Arguments{[C.Reference{token,3,typ}],[C.Parameter{token,0,typ}],True{}},sigs) ==
    Done{H.Reads{[3],Nil{}}} : Result<S.Error,H.Reads>}

law erased_read_has_no_live_capture:
  for +token: S.Token
  for +typ: U32
  for q: U32
  for parameter: Bool
  for known: Maybe<&2,C.Term>
  {H.captures([C.Binding{token,3,q,typ,parameter,known}],H.Reads{[3],Nil{}}) ==
    [C.Binding{token,3,0,typ,False{},None{}}] : List<&2,C.Binding>}

law close_starts_with_an_empty_environment:
  for token: S.Token
  for +site: U32
  for +typ: U32
  for +level: U32
  for q: U32
  for domain: U32
  for +captures: List<&2,C.Binding>
  for +body: C.Term
  for +caller: List<&2,V.Entry>
  for +frames: List<&2,V.Frame>
  for book: C.Book
  {V.step(V.Evaluate{C.Closure{token,site,typ,level,q,domain,captures,body},caller,frames},book) ==
    Done{V.Capture{site,typ,level,captures,body,caller,Nil{},frames}} : Result<S.Error,V.State>}

law erased_capture_skips_lookup:
  for +site: U32
  for +typ: U32
  for +level: U32
  for token: S.Token
  for id: U32
  for domain: U32
  for parameter: Bool
  for known: Maybe<&2,C.Term>
  for +tail: List<&2,C.Binding>
  for +body: C.Term
  for +caller: List<&2,V.Entry>
  for +env: List<&2,V.Entry>
  for +frames: List<&2,V.Frame>
  for book: C.Book
  {V.step(V.Capture{site,typ,level,Con{C.Binding{token,id,0,domain,parameter,known},tail},body,caller,env,frames},book) ==
    Done{V.Capture{site,typ,level,tail,body,caller,env,frames}} : Result<S.Error,V.State>}

law apply_evaluates_the_function_first:
  for token: S.Token
  for arrow: U32
  for typ: U32
  for +function: C.Term
  for +argument: C.Term
  for +caller: List<&2,V.Entry>
  for +frames: List<&2,V.Frame>
  for book: C.Book
  {V.step(V.Evaluate{C.Invoke{token,arrow,typ,function,argument},caller,frames},book) ==
    Done{V.Evaluate{function,caller,Con{V.ApplyArgument{argument,caller},frames}}} : Result<S.Error,V.State>}

law apply_closure_retains_its_environment:
  for site: U32
  for typ: U32
  for +level: U32
  for +body: C.Term
  for +env: List<&2,V.Entry>
  for +argument: C.Term
  for +caller: List<&2,V.Entry>
  for +frames: List<&2,V.Frame>
  {V.apply_argument(V.Closure{site,typ,level,body,env},argument,caller,frames) ==
    Done{V.Evaluate{argument,caller,Con{V.ApplyBody{level,body,env},frames}}} : Result<S.Error,V.State>}

law apply_enters_the_body_without_a_return_frame:
  for +value: V.Value
  for +level: U32
  for +body: C.Term
  for +env: List<&2,V.Entry>
  for +frames: List<&2,V.Frame>
  for book: C.Book
  {V.step(V.Return{value,Con{V.ApplyBody{level,body,env},frames}},book) ==
    Done{V.Evaluate{body,Con{V.Entry{level,value},env},frames}} : Result<S.Error,V.State>}

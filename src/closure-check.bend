import Base
import ./syntax.bend as S
import ./core.bend as C
import ./catalog.bend as G
import ./scope.bend as E

# Uses enforce affinity. Reads retain the separate erased/live capture layout.
type Reads is Data:
  Reads{all: List<&2,U32>, live: List<&2,U32>}
type Scan is Data:
  One{term: C.Term, live: Bool}
  Many{terms: List<&2,C.Term>, live: Bool}
  Arguments{terms: List<&2,C.Term>, parameters: List<&2,C.Parameter>, live: Bool}
type Prefix is Data:
  Prefix{parameters: List<&2,C.Parameter>, arguments: List<&2,S.Node>, missing: List<&2,C.Parameter>, rest: List<&2,S.Node>}
type Typed is Data:
  Typed{term: C.Term, type_id: U32}

def exact_arity(reference: G.FunctionRef, args: List<&2,S.Node>) -> Bool:
  match reference:
    case G.FunctionRef{index,C.Signature{name,params,result}}:
      Nat.is_eq(List.length(&2,C.Parameter,params),List.length(&2,S.Node,args))

def named(sigs: List<&2,C.Signature>, +token: S.Token) -> Bool:
  match sigs:
    case Nil{}: False{}
    case Con{C.Signature{name,params,result},tail}:
      Bool.or(String.eq(S.text(name),S.text(token)),named(tail,token))

def signature(sigs: List<&2,C.Signature>, +index: U32) -> Result<S.Error,C.Signature>:
  match sigs:
    case Nil{}: C.internal(C.Signature,"closure-signature")
    case Con{+head,+tail}:
      S.choose(Result<S.Error,C.Signature>,U32.is_eq(index,0),u => Done{head},u => signature(tail,U32.sub(index,1)))

def require_arrow(+definition: C.Datatype, token: S.Token) -> Result<S.Error,C.Datatype>:
  match definition:
    case C.Arrow{name,domain,result}: Done{definition}
    case _: C.invalid(C.Datatype,"not-callable",token)

def arrow(types: List<&2,C.Datatype>, +index: U32, +token: S.Token) -> Result<S.Error,C.Datatype>:
  S.bind(C.Datatype,C.Datatype,G.type_at(types,index),definition => require_arrow(definition,token))

def arrow_id(types: List<&2,C.Datatype>, +domain: U32, +result: U32, +index: U32) -> Result<S.Error,U32>:
  match types:
    case Nil{}: C.internal(U32,"closure-type")
    case Con{C.Arrow{token,a,b},+tail}:
      S.choose(Result<S.Error,U32>,Bool.and(U32.is_eq(a,domain),U32.is_eq(b,result)),u => Done{index},u => arrow_id(tail,domain,result,U32.add(index,1)))
    case Con{head,tail}: arrow_id(tail,domain,result,U32.add(index,1))

def unite(left: Reads, right: Reads) -> Reads:
  match left right:
    case Reads{a,b} Reads{c,d}: Reads{E.alternatives(a,c),E.alternatives(b,d)}

def empty() -> Reads:
  Reads{Nil{},Nil{}}

def captured(bindings: List<&2,C.Binding>, +live: Bool) -> Reads:
  match bindings:
    case Nil{}: empty()
    case Con{C.Binding{token,+level,q,typ,param,known},tail}:
      unite(Reads{[level],S.choose(List<&2,U32>,Bool.and(live,U32.is_ne(q,0)),u => [level],u => Nil{})},captured(tail,live))

def call_scan(sig: C.Signature, args: List<&2,C.Term>, live: Bool) -> Scan:
  match sig:
    case C.Signature{token,params,result}: Arguments{args,params,live}

# A nested close reads its environment; its bound body belongs to its own site.
def scan(fuel: Nat, mode: Scan, +sigs: List<&2,C.Signature>) -> Result<S.Error,Reads>:
  match fuel mode:
    case 0n _: Fail{S.Exhausted{"check",S.At{0,0,0,0}}}
    case 1n+ +n One{C.Reference{token,+level,type_id},live}:
      Done{Reads{[level],Bool.pick(List<&2,U32>,live,[level],Nil{})}}
    case 1n+ +n One{C.Value{token,type_id,tag},live}: Done{empty()}
    case 1n+ +n One{C.Closure{token,site,typ,level,q,domain,captures,body},live}:
      Done{captured(captures,live)}
    case 1n+ +n One{C.Invoke{token,arrow,typ,function,argument},live}:
      scan(n,Many{[function,argument],live},sigs)
    case 1n+ +n One{C.Construct{token,typ,tag,params,args},live}:
      scan(n,Arguments{args,params,live},sigs)
    case 1n+ +n One{C.Application{token,index,typ,+args},+live}:
      S.bind(C.Signature,Reads,signature(sigs,index),sig => scan(n,call_scan(sig,args,live),sigs))
    case 1n+ +n One{C.Let{token,level,q,typ,value,+body},+live}:
      S.bind(Reads,Reads,scan(n,One{value,Bool.and(live,U32.is_ne(q,0))},sigs),+a =>
        S.bind(Reads,Reads,scan(n,One{body,live},sigs),b => Done{unite(a,b)}))
    case 1n+ +n One{C.Case{token,+level,typ,arms},+live}:
      S.bind(Reads,Reads,scan(n,Many{arms,live},sigs),b =>
        Done{unite(Reads{[level],Bool.pick(List<&2,U32>,live,[level],Nil{})},b)})
    case 1n+ +n One{C.Branch{tag,fields,body},live}: scan(n,One{body,live},sigs)
    case 1n+ +n One{C.Sequence{items},live}: scan(n,Many{items,live},sigs)
    case 1n+ +n Many{Nil{},live}: Done{empty()}
    case 1n+ +n Many{Con{head,+tail},+live}:
      S.bind(Reads,Reads,scan(n,One{head,live},sigs),+a =>
        S.bind(Reads,Reads,scan(n,Many{tail,live},sigs),b => Done{unite(a,b)}))
    case 1n+ +n Arguments{Nil{},Nil{},live}: Done{empty()}
    case 1n+ +n Arguments{Con{head,+tail},Con{C.Parameter{token,q,typ},+params},+live}:
      S.bind(Reads,Reads,scan(n,One{head,Bool.and(live,U32.is_ne(q,0))},sigs),+a =>
        S.bind(Reads,Reads,scan(n,Arguments{tail,params,live},sigs),b => Done{unite(a,b)}))
    case 1n+ +n Arguments{args,params,live}: C.internal(Reads,"capture-arity")

def captures(bindings: List<&2,C.Binding>, +reads: Reads) -> List<&2,C.Binding>:
  match bindings reads:
    case Nil{} _: Nil{}
    case Con{C.Binding{+token,+level,+q,+typ,param,known},+tail} Reads{all,+live}:
      S.choose(List<&2,C.Binding>,E.contains(all,level),u =>
        Con{C.Binding{token,level,Bool.pick(U32,E.contains(live,level),q,0),typ,False{},None{}},captures(tail,reads)},u => captures(tail,reads))

def site(at: S.At, owner: U32, slot: U32) -> U32:
  match at:
    case S.At{start,end,line,column}: U32.add(U32.mul(U32.add(U32.mul(owner,65536),start),256),slot)

def close(checked: C.Checked, +token: S.Token, +code: U32, +typ: U32, +level: U32, +q: U32, +domain: U32,
  +bindings: List<&2,C.Binding>, sigs: List<&2,C.Signature>, fuel: Nat) -> Result<S.Error,C.Checked>:
  match checked:
    case C.Checked{+body,result,+uses}:
      S.bind(Reads,C.Checked,scan(fuel,One{body,True{}},sigs),reads =>
        Done{C.Checked{C.Closure{token,code,typ,level,q,domain,captures(bindings,reads),body},typ,E.remove(uses,level)}})

def sealed(bindings: List<&2,C.Binding>) -> List<&2,C.Binding>:
  match bindings:
    case Nil{}: Nil{}
    case Con{C.Binding{token,level,q,typ,param,known},tail}:
      Con{C.Binding{token,level,q,typ,False{},known},sealed(tail)}

def lambda_scope(scope: E.Scope, token: S.Token, q: U32, domain: U32) -> E.Scope:
  match scope:
    case E.Scope{bindings,+next,open,live,smaller}:
      E.Scope{Con{C.Binding{token,next,q,domain,False{},None{}},sealed(bindings)},U32.add(next,1),Nil{},live,smaller}

def lambda_type(wanted: Maybe<&2,U32>, +token: S.Token, types: List<&2,C.Datatype>) -> Result<S.Error,C.Datatype>:
  match wanted:
    case None{}: C.invalid(C.Datatype,"annotation-required",token)
    case Some{index}: arrow(types,index,token)

def prefix_head(value: Prefix, p: C.Parameter, a: S.Node) -> Prefix:
  match value:
    case Prefix{first,values,missing,rest}: Prefix{Con{p,first},Con{a,values},missing,rest}

def prefix(params: List<&2,C.Parameter>, args: List<&2,S.Node>) -> Prefix:
  match params args:
    case Nil{} rest: Prefix{Nil{},Nil{},Nil{},rest}
    case missing Nil{}: Prefix{Nil{},Nil{},missing,Nil{}}
    case Con{p,ps} Con{a,as}: prefix_head(prefix(ps,as),p,a)

def invoke(function: C.Checked, argument: C.Checked, +token: S.Token, +result: U32) -> Result<S.Error,C.Checked>:
  match function argument:
    case C.Checked{+head,+arrow,uses} C.Checked{+arg,domain,rest}:
      S.bind(List<&2,U32>,C.Checked,E.sequential(uses,rest,token),merged =>
        Done{C.Checked{C.Invoke{token,arrow,result,head,arg},result,merged}})

# Eta expansion saves supplied arguments before closing over fresh lexical levels.
def slots(params: List<&2,C.Parameter>, +level: U32) -> List<&2,C.Binding>:
  match params:
    case Nil{}: Nil{}
    case Con{C.Parameter{token,q,typ},tail}:
      Con{C.Binding{token,level,q,typ,False{},None{}},slots(tail,U32.add(level,1))}

def references(bindings: List<&2,C.Binding>) -> List<&2,C.Term>:
  match bindings:
    case Nil{}: Nil{}
    case Con{C.Binding{token,level,q,typ,param,known},tail}:
      Con{C.Reference{token,level,typ},references(tail)}

def eta_close(value: Typed, +token: S.Token, +owner: U32, +slot: U32, +level: U32, +q: U32, +domain: U32,
  +bindings: List<&2,C.Binding>, +types: List<&2,C.Datatype>, +sigs: List<&2,C.Signature>, +fuel: Nat) -> Result<S.Error,Typed>:
  match value:
    case Typed{+body,result}:
      S.bind(U32,Typed,arrow_id(types,domain,result,0),+typ =>
        S.bind(Reads,Typed,scan(fuel,One{body,True{}},sigs),reads =>
          Done{Typed{C.Closure{token,site(S.at(token),owner,slot),typ,level,q,domain,captures(bindings,reads),body},typ}}))

def eta(fuel: Nat, params: List<&2,C.Parameter>, +token: S.Token, +index: U32, +result: U32,
  +owner: U32, +slot: U32, +level: U32, +bindings: List<&2,C.Binding>, +args: List<&2,C.Term>, +catalog: C.Catalog) -> Result<S.Error,Typed>:
  match fuel params catalog:
    case 0n _ _: Fail{S.Exhausted{"check",S.at(token)}}
    case 1n+ +n Nil{} _: Done{Typed{C.Application{token,index,result,args},result}}
    case 1n+ +n Con{C.Parameter{+name,+q,+domain},tail} C.Catalog{+types,+sigs}:
      S.choose(Result<S.Error,Typed>,U32.is_eq(q,0),u => C.unsupported(Typed,"function-quantity",token),u =>
      S.choose(Result<S.Error,Typed>,U32.is_lt(level,4096),u =>
        S.bind(Typed,Typed,eta(n,tail,token,index,result,owner,U32.add(slot,1),U32.add(level,1),
          Con{C.Binding{name,level,q,domain,False{},None{}},bindings},
          List.append(&2,C.Term,args,[C.Reference{name,level,domain}]),catalog),body =>
            eta_close(body,token,owner,slot,level,q,domain,bindings,types,sigs,1n+n)),u => C.exhausted(Typed,token)))

def save(bindings: List<&2,C.Binding>, args: List<&2,C.Term>, +body: C.Term) -> Result<S.Error,C.Term>:
  match bindings args:
    case Nil{} Nil{}: Done{body}
    case Con{C.Binding{+token,+level,+q,+typ,param,known},tail} Con{+head,rest}:
      S.bind(C.Term,C.Term,save(tail,rest,body),next => Done{C.Let{token,level,q,typ,head,next}})
    case _ _: C.internal(C.Term,"partial-arity")

def saved(value: Typed, bindings: List<&2,C.Binding>, args: List<&2,C.Term>, +uses: List<&2,U32>) -> Result<S.Error,C.Checked>:
  match value:
    case Typed{body,+typ}:
      S.bind(C.Term,C.Checked,save(bindings,args,body),term => Done{C.Checked{term,typ,uses}})

def partial(value: C.Checked, +token: S.Token, +index: U32, +result: U32, +params: List<&2,C.Parameter>,
  +missing: List<&2,C.Parameter>, +owner: U32, scope: E.Scope, +catalog: C.Catalog, +fuel: Nat) -> Result<S.Error,C.Checked>:
  match value scope:
    case C.Checked{C.Sequence{+args},ignored,+uses} E.Scope{bindings,+next,open,live,smaller}:
      +bound = slots(params,next)
      S.bind(Typed,C.Checked,eta(fuel,missing,token,index,result,owner,0,
        U32.add(next,U32.from_nat(List.length(&2,C.Parameter,params))),bound,references(bound),catalog),body => saved(body,bound,args,uses))
    case _ _: C.internal(C.Checked,"partial-arguments")

def arity_kind(definition: C.Datatype, token: S.Token) -> Result<S.Error,Unit>:
  match definition:
    case C.Arrow{name,domain,result}: Done{Unit{}}
    case _: C.invalid(Unit,"call-arity",token)

def arity(wanted: Maybe<&2,U32>, +token: S.Token, types: List<&2,C.Datatype>) -> Result<S.Error,Unit>:
  match wanted:
    case None{}: Done{Unit{}}
    case Some{typ}:
      S.bind(C.Datatype,Unit,G.type_at(types,typ),definition => arity_kind(definition,token))

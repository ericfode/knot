import Base
import ./syntax.bend as S
import ./core.bend as C

type Inventory is Data:
  Inventory{sites: List<&2,C.Term>, arrows: List<&2,U32>}
type Dispatch is Data:
  Dispatch{token: S.Token, type_id: U32, index: U32, domain: U32, result: U32, sites: List<&2,U32>}
type Rename is Data:
  Same{}
  Shift{binder: U32}
type Plan is Data:
  Plan{book: C.Book, exports: U32, heap: List<&2,U32>, active: Bool}

def internal(-A: Type, code: String) -> Result<S.Error,A>:
  Fail{S.Internal{"closure",code}}

def includes(ids: List<&2,U32>, +id: U32) -> Bool:
  match ids:
    case Nil{}: False{}
    case Con{head,tail}: Bool.or(U32.is_eq(head,id),includes(tail,id))

def remember(+ids: List<&2,U32>, +id: U32) -> List<&2,U32>:
  S.choose(List<&2,U32>,includes(ids,id),u => ids,u => Con{id,ids})

def contains(sites: List<&2,C.Term>, +id: U32) -> Bool:
  match sites:
    case Nil{}: False{}
    case Con{C.Closure{token,site,typ,level,q,domain,captures,body},tail}:
      Bool.or(U32.is_eq(site,id),contains(tail,id))
    case Con{head,tail}: contains(tail,id)

def retain(+sites: List<&2,C.Term>, +term: C.Term, +id: U32) -> List<&2,C.Term>:
  S.choose(List<&2,C.Term>,contains(sites,id),u => sites,u => List.append(&2,C.Term,sites,[term]))

def add_site(old: Inventory, +term: C.Term, id: U32, typ: U32) -> Inventory:
  match old:
    case Inventory{sites,arrows}: Inventory{retain(sites,term,id),remember(arrows,typ)}

def add_arrow(old: Inventory, id: U32) -> Inventory:
  match old:
    case Inventory{sites,arrows}: Inventory{sites,remember(arrows,id)}

def scan(fuel: Nat, term: C.Term, +old: Inventory) -> Result<S.Error,Inventory>:
  match fuel term:
    case 0n _: Fail{S.Exhausted{"emit",S.At{0,0,0,0}}}
    case 1n+ n C.Closure{+token,+site,+typ,+level,+q,+domain,+captures,+body}:
      scan(n,body,add_site(old,C.Closure{token,site,typ,level,q,domain,captures,body},site,typ))
    case 1n+ n C.Invoke{token,arrow,typ,function,argument}:
      scan(n,C.Sequence{[function,argument]},add_arrow(old,arrow))
    case 1n+ n C.Construct{token,typ,tag,fields,args}: scan(n,C.Sequence{args},old)
    case 1n+ n C.Application{token,index,typ,args}: scan(n,C.Sequence{args},old)
    case 1n+ n C.Let{token,level,q,typ,value,body}: scan(n,C.Sequence{[value,body]},old)
    case 1n+ n C.Case{token,level,typ,arms}: scan(n,C.Sequence{arms},old)
    case 1n+ n C.Branch{tag,fields,body}: scan(n,body,old)
    case 1n+ n C.Sequence{Nil{}}: Done{old}
    case 1n+ +n C.Sequence{Con{head,+tail}}:
      S.bind(Inventory,Inventory,scan(n,head,old),next => scan(n,C.Sequence{tail},next))
    case 1n+ n other: Done{old}

def inventory(functions: List<&2,C.Function>, +depth: Nat, old: Inventory) -> Result<S.Error,Inventory>:
  match functions:
    case Nil{}: Done{old}
    case Con{C.Function{signature,body},+tail}:
      S.bind(Inventory,Inventory,scan(depth,body,old),next => inventory(tail,depth,next))

def site_ids(sites: List<&2,C.Term>, +typ: U32) -> List<&2,U32>:
  match sites:
    case Nil{}: Nil{}
    case Con{C.Closure{token,+site,id,level,q,domain,captures,body},+tail}:
      S.choose(List<&2,U32>,U32.is_eq(id,typ),u => Con{site,site_ids(tail,typ)},u => site_ids(tail,typ))
    case Con{head,tail}: site_ids(tail,typ)

def dispatches(types: List<&2,C.Datatype>, +used: List<&2,U32>, +sites: List<&2,C.Term>, +type_id: U32, +index: U32) -> List<&2,Dispatch>:
  match types:
    case Nil{}: Nil{}
    case Con{C.Arrow{+token,+domain,+result},+tail}:
      S.choose(List<&2,Dispatch>,includes(used,type_id),u =>
        Con{Dispatch{token,type_id,index,domain,result,site_ids(sites,type_id)},dispatches(tail,used,sites,U32.add(type_id,1),U32.add(index,1))},u =>
        dispatches(tail,used,sites,U32.add(type_id,1),index))
    case Con{head,tail}: dispatches(tail,used,sites,U32.add(type_id,1),index)

def lookup(table: List<&2,Dispatch>, +typ: U32) -> Result<S.Error,U32>:
  match table:
    case Nil{}: internal(U32,"missing-dispatch")
    case Con{Dispatch{token,id,+index,domain,result,sites},+tail}:
      S.choose(Result<S.Error,U32>,U32.is_eq(id,typ),u => Done{index},u => lookup(tail,typ))

def site_index(ids: List<&2,U32>, +site: U32, +index: U32) -> Result<S.Error,U32>:
  match ids:
    case Nil{}: internal(U32,"missing-site")
    case Con{id,+tail}:
      S.choose(Result<S.Error,U32>,U32.is_eq(id,site),u => Done{index},u => site_index(tail,site,U32.add(index,1)))

def ordinal(table: List<&2,Dispatch>, +typ: U32, +site: U32) -> Result<S.Error,U32>:
  match table:
    case Nil{}: internal(U32,"missing-dispatch")
    case Con{Dispatch{token,id,index,domain,result,+sites},+tail}:
      S.choose(Result<S.Error,U32>,U32.is_eq(id,typ),u => site_index(sites,site,0),u => ordinal(tail,typ,site))

def level(rename: Rename, +id: U32) -> U32:
  match rename:
    case Same{}: id
    case Shift{binder}: Bool.pick(U32,U32.is_eq(binder,id),1,U32.add(id,2))

def capture_params(bindings: List<&2,C.Binding>) -> List<&2,C.Parameter>:
  match bindings:
    case Nil{}: Nil{}
    case Con{C.Binding{token,id,q,typ,param,known},tail}:
      Con{C.Parameter{token,q,typ},capture_params(tail)}

def capture_args(bindings: List<&2,C.Binding>, +rename: Rename) -> List<&2,C.Term>:
  match bindings:
    case Nil{}: Nil{}
    case Con{C.Binding{token,id,q,typ,param,known},tail}:
      Con{C.Reference{token,level(rename,id),typ},capture_args(tail,rename)}

def fields(bindings: List<&2,C.Binding>, +rename: Rename) -> List<&2,C.Binding>:
  match bindings:
    case Nil{}: Nil{}
    case Con{C.Binding{token,id,q,typ,param,known},tail}:
      Con{C.Binding{token,level(rename,id),q,typ,param,known},fields(tail,rename)}

# The cell stores each live capture once; erased signatures retain their slots.
def pack(token: S.Token, tag: U32, typ: U32, +captures: List<&2,C.Binding>, rename: Rename) -> C.Term:
  C.Construct{token,typ,tag,capture_params(captures),capture_args(captures,rename)}

def apply(token: S.Token, index: U32, result: U32, function: C.Term, argument: C.Term) -> C.Term:
  C.Application{token,index,result,[function,argument]}

def sequence(term: C.Term, next: List<&2,C.Term> -> Result<S.Error,C.Term>) -> Result<S.Error,C.Term>:
  match term:
    case C.Sequence{items}: next(items)
    case other: internal(C.Term,"sequence-node")

# Site bodies are rewritten separately. A nested close remaps its captures,
# never the nested site's binder; each dispatcher owns its own level map.
def rewrite(fuel: Nat, term: C.Term, +rename: Rename, +table: List<&2,Dispatch>) -> Result<S.Error,C.Term>:
  match fuel term:
    case 0n _: Fail{S.Exhausted{"emit",S.At{0,0,0,0}}}
    case 1n+ n C.Value{token,typ,tag}: Done{C.Value{token,typ,tag}}
    case 1n+ n C.Reference{token,id,typ}: Done{C.Reference{token,level(rename,id),typ}}
    case 1n+ n C.Closure{+token,site,+typ,id,q,domain,+captures,body}:
      S.bind(U32,C.Term,ordinal(table,typ,site),tag => Done{pack(token,tag,typ,captures,rename)})
    case 1n+ +n C.Invoke{+token,arrow,+typ,+function,+argument}:
      S.bind(U32,C.Term,lookup(table,arrow),+index =>
        S.bind(C.Term,C.Term,rewrite(n,function,rename,table),+callee =>
          S.bind(C.Term,C.Term,rewrite(n,argument,rename,table),value => Done{apply(token,index,typ,callee,value)})))
    case 1n+ n C.Construct{+token,+typ,+tag,+params,args}:
      S.bind(C.Term,C.Term,rewrite(n,C.Sequence{args},rename,table),value =>
        sequence(value,items => Done{C.Construct{token,typ,tag,params,items}}))
    case 1n+ n C.Application{+token,+index,+typ,args}:
      S.bind(C.Term,C.Term,rewrite(n,C.Sequence{args},rename,table),value =>
        sequence(value,items => Done{C.Application{token,index,typ,items}}))
    case 1n+ +n C.Let{+token,id,+q,+typ,value,+body}:
      +mapped = level(rename,id)
      S.bind(C.Term,C.Term,rewrite(n,value,rename,table),+initial =>
        S.bind(C.Term,C.Term,rewrite(n,body,rename,table),result => Done{C.Let{token,mapped,q,typ,initial,result}}))
    case 1n+ n C.Case{+token,id,+typ,arms}:
      +mapped = level(rename,id)
      S.bind(C.Term,C.Term,rewrite(n,C.Sequence{arms},rename,table),value =>
        sequence(value,items => Done{C.Case{token,mapped,typ,items}}))
    case 1n+ n C.Branch{+tag,bindings,body}:
      +mapped = fields(bindings,rename)
      S.bind(C.Term,C.Term,rewrite(n,body,rename,table),value => Done{C.Branch{tag,mapped,value}})
    case 1n+ n C.Sequence{Nil{}}: Done{C.Sequence{Nil{}}}
    case 1n+ +n C.Sequence{Con{head,+tail}}:
      S.bind(C.Term,C.Term,rewrite(n,head,rename,table),+first =>
        S.bind(C.Term,C.Term,rewrite(n,C.Sequence{tail},rename,table),rest =>
          sequence(rest,items => Done{C.Sequence{Con{first,items}}})))

def functions(remaining: List<&2,C.Function>, +depth: Nat, +table: List<&2,Dispatch>) -> Result<S.Error,List<&2,C.Function>>:
  match remaining:
    case Nil{}: Done{Nil{}}
    case Con{C.Function{+signature,body},+tail}:
      S.bind(C.Term,List<&2,C.Function>,rewrite(depth,body,Same{},table),+term =>
        S.bind(List<&2,C.Function>,List<&2,C.Function>,functions(tail,depth,table),rest => Done{Con{C.Function{signature,term},rest}}))

def constructors(sites: List<&2,C.Term>, +typ: U32) -> List<&2,C.Constructor>:
  match sites:
    case Nil{}: Nil{}
    case Con{C.Closure{+token,site,id,level,q,domain,+captures,body},+tail}:
      S.choose(List<&2,C.Constructor>,U32.is_eq(id,typ),u =>
        Con{C.Constructor{token,capture_params(captures)},constructors(tail,typ)},u => constructors(tail,typ))
    case Con{head,tail}: constructors(tail,typ)

def types(remaining: List<&2,C.Datatype>, +sites: List<&2,C.Term>, +id: U32) -> List<&2,C.Datatype>:
  match remaining:
    case Nil{}: Nil{}
    case Con{C.Arrow{token,domain,result},tail}:
      Con{C.Datatype{token,False{},constructors(sites,id)},types(tail,sites,U32.add(id,1))}
    case Con{head,tail}: Con{head,types(tail,sites,U32.add(id,1))}

def dispatch_arm(tag: U32, captures: List<&2,C.Binding>, binder: U32, body: C.Term) -> C.Term:
  C.Branch{tag,fields(captures,Shift{binder}),body}

def arms(sites: List<&2,C.Term>, +typ: U32, +tag: U32, +depth: Nat, +table: List<&2,Dispatch>) -> Result<S.Error,List<&2,C.Term>>:
  match sites:
    case Nil{}: Done{Nil{}}
    case Con{C.Closure{token,site,id,+binder,q,domain,+captures,+body},+tail}:
      S.choose(Result<S.Error,List<&2,C.Term>>,U32.is_eq(id,typ),u =>
        S.bind(C.Term,List<&2,C.Term>,rewrite(depth,body,Shift{binder},table),+term =>
          S.bind(List<&2,C.Term>,List<&2,C.Term>,arms(tail,typ,U32.add(tag,1),depth,table),rest =>
            Done{Con{dispatch_arm(tag,captures,binder,term),rest}})),u => arms(tail,typ,tag,depth,table))
    case Con{head,tail}: arms(tail,typ,tag,depth,table)

def dispatcher(dispatch: Dispatch, +sites: List<&2,C.Term>, depth: Nat, table: List<&2,Dispatch>) -> Result<S.Error,C.Function>:
  match dispatch:
    case Dispatch{+token,+typ,index,+domain,+result,ids}:
      S.bind(List<&2,C.Term>,C.Function,arms(sites,typ,0,depth,table),branches =>
        Done{C.Function{C.Signature{token,[C.Parameter{token,1,typ},C.Parameter{token,1,domain}],result},C.Case{token,0,result,branches}}})

def dispatchers(remaining: List<&2,Dispatch>, +sites: List<&2,C.Term>, +depth: Nat, +table: List<&2,Dispatch>) -> Result<S.Error,List<&2,C.Function>>:
  match remaining:
    case Nil{}: Done{Nil{}}
    case Con{head,+tail}:
      S.bind(C.Function,List<&2,C.Function>,dispatcher(head,sites,depth,table),+first =>
        S.bind(List<&2,C.Function>,List<&2,C.Function>,dispatchers(tail,sites,depth,table),rest => Done{Con{first,rest}}))

def prepare(found: Inventory, +original: C.Book, +count: U32, +depth: Nat) -> Result<S.Error,Plan>:
  match found original:
    case Inventory{sites,Nil{}} book: Done{Plan{book,count,Nil{},False{}}}
    case Inventory{+sites,+used} C.Book{+datatypes,+definitions}:
      +table = dispatches(datatypes,used,sites,0,count)
      S.bind(List<&2,C.Function>,Plan,functions(definitions,depth,table),+originals =>
        S.bind(List<&2,C.Function>,Plan,dispatchers(table,sites,depth,table),generated =>
          Done{Plan{C.Book{types(datatypes,sites,0),List.append(&2,C.Function,originals,generated)},count,used,True{}}}))

def run(+book: C.Book, +depth: Nat) -> Result<S.Error,Plan>:
  match book:
    case C.Book{+types,+functions}:
      +count = U32.from_nat(List.length(&2,C.Function,functions))
      S.bind(Inventory,Plan,inventory(functions,depth,Inventory{Nil{},Nil{}}),found => prepare(found,C.Book{types,functions},count,depth))

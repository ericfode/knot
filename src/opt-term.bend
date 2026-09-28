import Base
import ./syntax.bend as S
import ./core.bend as C

def internal(-A: Type, code: String) -> Result<S.Error,A>:
  Fail{S.Internal{"opt",code}}

def exhausted(-A: Type) -> Result<S.Error,A>:
  Fail{S.Exhausted{"opt",S.At{0,0,0,0}}}

def terms(value: C.Term, next: List<&2,C.Term> -> Result<S.Error,C.Term>) -> Result<S.Error,C.Term>:
  match value:
    case C.Sequence{items}: next(items)
    case _: internal(C.Term,"term-list")

type Measure is Data:
  Size{}
  Ceiling{}
  Uses{level: U32}
  Calls{index: U32}

def maximum(+a: U32, +b: U32) -> U32:
  Bool.pick(U32,U32.is_ge(a,b),a,b)

# Saturation makes the same walk a size budget and a bounded occurrence query.
def combine(kind: Measure, a: U32, b: U32) -> U32:
  match kind:
    case Ceiling{}: maximum(a,b)
    case _: U32.min(4097,U32.add(a,b))

def atom(kind: Measure, level: Maybe<&2,U32>, call: Maybe<&2,U32>) -> U32:
  match kind level call:
    case Size{} _ _: 1
    case Ceiling{} Some{x} _: U32.add(x,1)
    case Uses{a} Some{b} _: Bool.pick(U32,U32.is_eq(a,b),1,0)
    case Calls{a} _ Some{b}: Bool.pick(U32,U32.is_eq(a,b),1,0)
    case _ _ _: 0

def field_ceiling(fields: List<&2,C.Binding>) -> U32:
  match fields:
    case Nil{}: 0
    case Con{C.Binding{token,level,q,typ,param,known},tail}: maximum(U32.add(level,1),field_ceiling(tail))

def binding_size(+kind: Measure, level: U32, size: U32) -> U32:
  match kind:
    case Ceiling{}: maximum(level,size)
    case _: combine(kind,atom(kind,None{},None{}),size)

def measure(fuel: Nat, term: C.Term, +kind: Measure) -> Result<S.Error,U32>:
  match fuel term:
    case 0n _: exhausted(U32)
    case 1n+ +n C.Value{token,typ,tag}: Done{atom(kind,None{},None{})}
    case 1n+ +n C.Reference{token,level,typ}: Done{atom(kind,Some{level},None{})}
    case 1n+ +n C.Construct{token,typ,tag,fields,args}:
      S.bind(U32,U32,measure(n,C.Sequence{args},kind),size => Done{combine(kind,atom(kind,None{},None{}),size)})
    case 1n+ +n C.Application{token,index,typ,args}:
      S.bind(U32,U32,measure(n,C.Sequence{args},kind),size => Done{combine(kind,atom(kind,None{},Some{index}),size)})
    case 1n+ +n C.Let{token,+level,q,typ,value,body}:
      S.bind(U32,U32,measure(n,C.Sequence{[value,body]},kind),size => Done{binding_size(kind,U32.add(level,1),size)})
    case 1n+ +n C.Case{token,level,typ,arms}:
      S.bind(U32,U32,measure(n,C.Sequence{arms},kind),size => Done{combine(kind,atom(kind,Some{level},None{}),size)})
    case 1n+ +n C.Branch{tag,+fields,body}:
      S.bind(U32,U32,measure(n,body,kind),size => Done{binding_size(kind,field_ceiling(fields),size)})
    case 1n+ +n C.Sequence{Nil{}}: Done{0}
    case 1n+ +n C.Sequence{Con{head,+tail}}:
      S.bind(U32,U32,measure(n,head,kind),left =>
        S.bind(U32,U32,measure(n,C.Sequence{tail},kind),right => Done{combine(kind,left,right)}))
    case 1n+n _: Fail{S.Unsupported{"opt","term",S.At{0,0,0,0}}}

def fields_shift(fields: List<&2,C.Binding>, +offset: U32) -> List<&2,C.Binding>:
  match fields:
    case Nil{}: Nil{}
    case Con{C.Binding{token,level,q,typ,param,known},tail}:
      Con{C.Binding{token,U32.add(level,offset),q,typ,param,None{}},fields_shift(tail,offset)}

# Callers establish offset + Ceiling(body) <= 4096. Translation preserves all
# lexical equalities; sibling branch scopes remain separate. known is a cache.
def shift(fuel: Nat, term: C.Term, +offset: U32) -> Result<S.Error,C.Term>:
  match fuel term:
    case 0n _: exhausted(C.Term)
    case 1n+ +n C.Value{token,typ,tag}: Done{C.Value{token,typ,tag}}
    case 1n+ +n C.Reference{token,level,typ}: Done{C.Reference{token,U32.add(level,offset),typ}}
    case 1n+ +n C.Construct{+token,+typ,+tag,+fields,args}:
      S.bind(C.Term,C.Term,shift(n,C.Sequence{args},offset),list => terms(list,xs => Done{C.Construct{token,typ,tag,fields,xs}}))
    case 1n+ +n C.Application{+token,+index,+typ,args}:
      S.bind(C.Term,C.Term,shift(n,C.Sequence{args},offset),list => terms(list,xs => Done{C.Application{token,index,typ,xs}}))
    case 1n+ +n C.Let{+token,+level,+q,+typ,value,+body}:
      S.bind(C.Term,C.Term,shift(n,value,offset),initial =>
        S.bind(C.Term,C.Term,shift(n,body,offset),rest => Done{C.Let{token,U32.add(level,offset),q,typ,initial,rest}}))
    case 1n+ +n C.Case{+token,level,+typ,arms}:
      +mapped = U32.add(level,offset)
      S.bind(C.Term,C.Term,shift(n,C.Sequence{arms},offset),list => terms(list,xs => Done{C.Case{token,mapped,typ,xs}}))
    case 1n+ +n C.Branch{+tag,fields,body}:
      +mapped = fields_shift(fields,offset)
      S.bind(C.Term,C.Term,shift(n,body,offset),rest => Done{C.Branch{tag,mapped,rest}})
    case 1n+ +n C.Sequence{Nil{}}: Done{C.Sequence{Nil{}}}
    case 1n+ +n C.Sequence{Con{head,+tail}}:
      S.bind(C.Term,C.Term,shift(n,head,offset),first =>
        S.bind(C.Term,C.Term,shift(n,C.Sequence{tail},offset),list => terms(list,xs => Done{C.Sequence{Con{first,xs}}})))
    case 1n+n _: Fail{S.Unsupported{"opt","term",S.At{0,0,0,0}}}

def parameters_equal(left: List<&2,C.Parameter>, right: List<&2,C.Parameter>) -> Bool:
  match left right:
    case Nil{} Nil{}: True{}
    case Con{C.Parameter{token,q,typ},tail} Con{C.Parameter{other,r,target},rest}:
      Bool.and(U32.is_eq(q,r),Bool.and(U32.is_eq(typ,target),parameters_equal(tail,rest)))
    case _ _: False{}

def fields_equal(left: List<&2,C.Binding>, right: List<&2,C.Binding>) -> Bool:
  match left right:
    case Nil{} Nil{}: True{}
    case Con{C.Binding{token,level,q,typ,param,known},tail} Con{C.Binding{other,id,r,target,mark,cached},rest}:
      Bool.and(U32.is_eq(level,id),Bool.and(U32.is_eq(q,r),Bool.and(U32.is_eq(typ,target),fields_equal(tail,rest))))
    case _ _: False{}

# Compare the tree directly: a textual fixed-point test creates a host stack
# proportional to rendered bytes. Tokens and refinement caches are not identity.
def equal(fuel: Nat, left: C.Term, right: C.Term) -> Result<S.Error,Bool>:
  match fuel left right:
    case 0n _ _: exhausted(Bool)
    case 1n+n C.Value{token,typ,tag} C.Value{other,target,ordinal}:
      Done{Bool.and(U32.is_eq(typ,target),U32.is_eq(tag,ordinal))}
    case 1n+n C.Reference{token,level,typ} C.Reference{other,id,target}:
      Done{Bool.and(U32.is_eq(level,id),U32.is_eq(typ,target))}
    case 1n+ +n C.Construct{token,typ,tag,fields,+args} C.Construct{other,target,ordinal,params,+xs}:
      S.choose(Result<S.Error,Bool>,Bool.and(U32.is_eq(typ,target),Bool.and(U32.is_eq(tag,ordinal),parameters_equal(fields,params))),u => equal(n,C.Sequence{args},C.Sequence{xs}),u => Done{False{}})
    case 1n+ +n C.Application{token,index,typ,+args} C.Application{other,id,target,+xs}:
      S.choose(Result<S.Error,Bool>,Bool.and(U32.is_eq(index,id),U32.is_eq(typ,target)),u => equal(n,C.Sequence{args},C.Sequence{xs}),u => Done{False{}})
    case 1n+ +n C.Let{token,level,q,typ,+value,+body} C.Let{other,id,r,target,+initial,+rest}:
      S.choose(Result<S.Error,Bool>,Bool.and(U32.is_eq(level,id),Bool.and(U32.is_eq(q,r),U32.is_eq(typ,target))),u => equal(n,C.Sequence{[value,body]},C.Sequence{[initial,rest]}),u => Done{False{}})
    case 1n+ +n C.Case{token,level,typ,+arms} C.Case{other,id,target,+branches}:
      S.choose(Result<S.Error,Bool>,Bool.and(U32.is_eq(level,id),U32.is_eq(typ,target)),u => equal(n,C.Sequence{arms},C.Sequence{branches}),u => Done{False{}})
    case 1n+ +n C.Branch{tag,fields,+body} C.Branch{ordinal,params,+term}:
      S.choose(Result<S.Error,Bool>,Bool.and(U32.is_eq(tag,ordinal),fields_equal(fields,params)),u => equal(n,body,term),u => Done{False{}})
    case 1n+n C.Sequence{Nil{}} C.Sequence{Nil{}}: Done{True{}}
    case 1n+ +n C.Sequence{Con{head,+tail}} C.Sequence{Con{term,+rest}}:
      S.bind(Bool,Bool,equal(n,head,term),same =>
        S.choose(Result<S.Error,Bool>,same,u => equal(n,C.Sequence{tail},C.Sequence{rest}),u => Done{False{}}))
    case _ _ _: Done{False{}}

def bodies_equal(left: List<&2,C.Function>, right: List<&2,C.Function>, +depth: Nat) -> Result<S.Error,Bool>:
  match left right:
    case Nil{} Nil{}: Done{True{}}
    case Con{C.Function{sig,a},+tail} Con{C.Function{signature,b},+rest}:
      S.bind(Bool,Bool,equal(depth,a,b),same =>
        S.choose(Result<S.Error,Bool>,same,u => bodies_equal(tail,rest,depth),u => Done{False{}}))
    case _ _: Done{False{}}

def stable(left: C.Book, right: C.Book, depth: Nat) -> Result<S.Error,Bool>:
  match left right:
    case C.Book{types,a} C.Book{other,b}: bodies_equal(a,b,depth)

import Base
import ./syntax.bend as S
import ./core.bend as C
import ./primitive-op.bend as R
import ./primitive.bend as O
import ./literal-types.bend as L

type Instruction is Data:
  Instruction{op: U32, a: U32, b: U32, c: U32, next: U32}
type Assembly is Data:
  Assembly{entry: U32, count: U32, slots: U32, reversed: List<&2,Instruction>}
type Entry is Data:
  Entry{signature: C.Signature, entry: U32, slots: U32}
type Module is Data:
  Module{entries: List<&2,Entry>, assembly: Assembly}
type Mode is Data:
  Term{term: C.Term}
  Arguments{terms: List<&2,C.Term>, parameters: List<&2,C.Parameter>, placeholders: Bool}
  Values{terms: List<&2,C.Term>}
  Text{codes: List<&2,U32>}
  Branches{arms: List<&2,C.Term>, level: U32, heap: Bool}
  Arm{arm: C.Term, level: U32, heap: Bool}
  Unpack{fields: List<&2,C.Binding>, level: U32, offset: U32, body: C.Term}

def internal(-A: Type, code: String) -> Result<S.Error,A>:
  Fail{S.Internal{"emit",code}}

def maximum(+a: U32, +b: U32) -> U32:
  Bool.pick(U32,U32.is_ge(a,b),a,b)

# Graph addresses are instruction indices, independent of layout order. Each
# emission installs one node and preserves every previously issued address.
def put(assembly: Assembly, +op: U32, +a: U32, b: U32, c: U32, next: U32) -> Result<S.Error,Assembly>:
  match assembly:
    case Assembly{entry,+count,+slots,code}:
      S.choose(Result<S.Error,Assembly>,U32.is_lt(count,32768),u =>
        Done{Assembly{count,U32.add(count,1),S.choose(U32,Bool.or(U32.is_eq(op,2),U32.is_eq(op,3)),u => maximum(slots,U32.add(a,1)),u => slots),
          Con{Instruction{op,a,b,c,next},code}}},u => Fail{S.Exhausted{"emit",S.At{0,0,0,0}}})

def then(result: Result<S.Error,Assembly>, next: U32 -> Assembly -> Result<S.Error,Assembly>) -> Result<S.Error,Assembly>:
  match result:
    case Fail{error}: Fail{error}
    case Done{Assembly{+entry,count,slots,code}}: next(entry,Assembly{entry,count,slots,code})

def signature(functions: List<&2,C.Function>, +index: U32) -> Result<S.Error,C.Signature>:
  match functions:
    case Nil{}: internal(C.Signature,"function-index")
    case Con{C.Function{+sig,body},+tail}:
      S.choose(Result<S.Error,C.Signature>,U32.is_eq(index,0),u => Done{sig},u => signature(tail,U32.sub(index,1)))

def parameters(signature: C.Signature) -> List<&2,C.Parameter>:
  match signature:
    case C.Signature{token,params,result}: params

def live(params: List<&2,C.Parameter>) -> U32:
  match params:
    case Nil{}: 0
    case Con{C.Parameter{token,q,typ},tail}: U32.add(Bool.pick(U32,U32.is_eq(q,0),0,1),live(tail))

def fielded(ctors: List<&2,C.Constructor>) -> Bool:
  match ctors:
    case Nil{}: False{}
    case Con{C.Constructor{token,Nil{}},tail}: fielded(tail)
    case _: True{}

def heap_types(types: List<&2,C.Datatype>, +index: U32) -> List<&2,U32>:
  match types:
    case Nil{}: Nil{}
    case Con{+definition,+tail}:
      match definition:
        case C.Datatype{token,data,ctors}:
          S.choose(List<&2,U32>,Bool.and(fielded(ctors),Bool.not(L.is_kind(Con{definition,Nil{}},0,2))),u =>
            Con{index,heap_types(tail,U32.add(index,1))},u => heap_types(tail,U32.add(index,1)))

def boxed(heap: List<&2,U32>, +id: U32) -> Bool:
  match heap:
    case Nil{}: False{}
    case Con{head,tail}: Bool.or(U32.is_eq(head,id),boxed(tail,id))

def fielded_arms(arms: List<&2,C.Term>) -> Bool:
  match arms:
    case Nil{}: False{}
    case Con{C.Branch{tag,Con{head,tail},body},rest}: True{}
    case Con{head,tail}: fielded_arms(tail)

def arm_test(arm: C.Term, +body: U32, +other: U32, +level: U32, +cell: Bool, assembly: Assembly) -> Result<S.Error,Assembly>:
  match arm:
    case C.Branch{tag,fields,term}:
      then(put(assembly,9,tag,body,other,0),+pc => +state =>
        S.choose(Result<S.Error,Assembly>,cell,u =>
          then(put(state,7,0,0,0,pc),pc => state => put(state,2,level,0,0,pc)),u => put(state,2,level,0,0,pc)))
    case _: internal(Assembly,"arm-test")

def lower(fuel: Nat, mode: Mode, +functions: List<&2,C.Function>, +heap: List<&2,U32>, +next: U32, +assembly: Assembly) -> Result<S.Error,Assembly>:
  match fuel mode:
    case 0n _: Fail{S.Exhausted{"emit",S.At{0,0,0,0}}}
    case 1n+n Term{C.Value{token,type_id,tag}}:
      put(assembly,Bool.pick(U32,boxed(heap,type_id),6,1),tag,0,0,next)
    case 1n+n Term{C.Literal{token,type_id,1,number,codes}}: put(assembly,11,number,0,0,next)
    case 1n+n Term{C.Literal{token,type_id,3,number,codes}}: lower(n,Text{codes},functions,heap,next,assembly)
    case 1n+ +n Term{C.Intrinsic{token,type_id,op,+args}}:
      then(put(assembly,5,O.code(op),U32.from_nat(List.length(&2,C.Term,args)),0,next),pc => state => lower(n,Values{args},functions,heap,pc,state))
    case 1n+ +n Term{C.Construct{token,type_id,tag,+params,args}}:
      then(put(assembly,6,tag,live(params),0,next),pc => state => lower(n,Arguments{args,params,False{}},functions,heap,pc,state))
    case 1n+n Term{C.Reference{token,level,type_id}}: put(assembly,2,level,0,0,next)
    case 1n+ +n Term{C.Application{token,+index,type_id,+args}}:
      S.bind(C.Signature,Assembly,signature(functions,index),sig =>
        then(put(assembly,4,index,0,0,next),pc => state => lower(n,Arguments{args,parameters(sig),True{}},functions,heap,pc,state)))
    case 1n+ +n Term{C.Let{token,+level,q,type_id,+value,+body}}:
      S.choose(Result<S.Error,Assembly>,U32.is_eq(q,0),u => lower(n,Term{body},functions,heap,next,assembly),u =>
        then(lower(n,Term{body},functions,heap,next,assembly),pc => state =>
          then(put(state,3,level,0,0,pc),after => saved => lower(n,Term{value},functions,heap,after,saved))))
    case 1n+n Term{C.Case{token,level,type_id,+arms}}:
      lower(n,Branches{arms,level,fielded_arms(arms)},functions,heap,next,assembly)
    case 1n+n Term{term}: internal(Assembly,"expression-node")
    case 1n+n Text{Nil{}}: put(assembly,1,0,0,0,next)
    case 1n+ +n Text{Con{head,tail}}:
      then(put(assembly,10,head,0,0,next),pc => state => lower(n,Text{tail},functions,heap,pc,state))
    case 1n+n Values{Nil{}}:
      match assembly:
        case Assembly{entry,count,slots,code}: Done{Assembly{next,count,slots,code}}
    case 1n+ +n Values{Con{+head,tail}}:
      then(lower(n,Values{tail},functions,heap,next,assembly),pc => state => lower(n,Term{head},functions,heap,pc,state))
    case 1n+n Arguments{Nil{},Nil{},placeholders}:
      match assembly:
        case Assembly{entry,count,slots,code}: Done{Assembly{next,count,slots,code}}
    case 1n+ +n Arguments{Con{+head,tail},Con{C.Parameter{token,+q,typ},params},+placeholders}:
      then(lower(n,Arguments{tail,params,placeholders},functions,heap,next,assembly),+pc => +state =>
        S.choose(Result<S.Error,Assembly>,U32.is_eq(q,0),u =>
          S.choose(Result<S.Error,Assembly>,placeholders,u => put(state,1,0,0,0,pc),u => Done{state}),u => lower(n,Term{head},functions,heap,pc,state)))
    case 1n+n Arguments{terms,params,placeholders}: internal(Assembly,"argument-arity")
    case 1n+n Branches{Con{head,Nil{}},level,cell}: lower(n,Arm{head,level,cell},functions,heap,next,assembly)
    case 1n+ +n Branches{Con{+head,+tail},+level,+cell}:
      then(lower(n,Branches{tail,level,cell},functions,heap,next,assembly),+other => state =>
        then(lower(n,Arm{head,level,cell},functions,heap,next,state),body => state =>
          arm_test(head,body,other,level,cell,state)))
    case 1n+n Branches{Nil{},level,cell}: internal(Assembly,"empty-case")
    case 1n+n Arm{C.Default{body},level,cell}: lower(n,Term{body},functions,heap,next,assembly)
    case 1n+n Arm{C.Branch{tag,fields,body},level,cell}: lower(n,Unpack{fields,level,4,body},functions,heap,next,assembly)
    case 1n+n Arm{term,level,cell}: internal(Assembly,"arm-node")
    case 1n+n Unpack{Nil{},level,offset,body}: lower(n,Term{body},functions,heap,next,assembly)
    case 1n+ +n Unpack{Con{C.Binding{token,+id,+q,typ,param,known},+fields},+level,+offset,+body}:
      S.choose(Result<S.Error,Assembly>,U32.is_eq(q,0),u => lower(n,Unpack{fields,level,offset,body},functions,heap,next,assembly),u =>
        then(lower(n,Unpack{fields,level,U32.add(offset,4),body},functions,heap,next,assembly),pc => state =>
          then(put(state,3,id,0,0,pc),pc => state =>
            then(put(state,7,offset,0,0,pc),pc => state => put(state,2,level,0,0,pc)))))

def reset(assembly: Assembly, slots: U32) -> Assembly:
  match assembly:
    case Assembly{entry,count,old,code}: Assembly{entry,count,slots,code}

def finished(signature: C.Signature, assembly: Assembly, done: List<&2,Entry>,
  next: Assembly -> List<&2,Entry> -> Result<S.Error,Module>) -> Result<S.Error,Module>:
  match assembly:
    case Assembly{+entry,count,+slots,code}:
      next(Assembly{entry,count,slots,code},Con{Entry{signature,entry,slots},done})

def functions(remaining: List<&2,C.Function>, +all: List<&2,C.Function>, +heap: List<&2,U32>, +depth: Nat,
  assembly: Assembly, +done: List<&2,Entry>) -> Result<S.Error,Module>:
  match remaining:
    case Nil{}: Done{Module{List.reverse(&2,Entry,done),assembly}}
    case Con{C.Function{+signature,body},+tail}:
      S.bind(Assembly,Module,lower(depth,Term{body},all,heap,0,reset(assembly,U32.from_nat(List.length(&2,C.Parameter,parameters(signature))))),state =>
        finished(signature,state,done,after => entries => functions(tail,all,heap,depth,after,entries)))

def book(value: C.Book, depth: Nat) -> Result<S.Error,Module>:
  match value:
    case C.Book{types,+funcs}:
      functions(funcs,funcs,heap_types(types,0),depth,Assembly{0,1,0,[Instruction{0,0,0,0,0}]},Nil{})

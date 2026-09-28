import Base
import ./syntax.bend as S
import ./core.bend as C
import ./wasm-bytes.bend as W

# A scope owns its live bindings; an activation owns a disjoint capture interval.
type Slot is Data:
  Slot{level: U32, capture: U32, retained: Bool}
type Record is Data:
  Op{code: U32, a: U32, b: U32, c: U32, d: U32, e: U32}
  Mark{label: U32}
type Plan is Data:
  Plan{code: List<&2,Record>, captures: U32, joins: U32, labels: U32, count: U32, arity: U32}
type Flow is Data:
  Flow{locals: List<&2,Slot>, next: U32, plan: Plan}
type Exit is Data:
  Finish{}
  Reply{join: U32, destination: U32}
type Activation is Data:
  Activation{index: U32, base: U32, entry: U32, recursive: Bool, exit: Exit}
type Mode is Data:
  Expression{term: C.Term, destination: U32}
  Body{term: C.Term}
  Arguments{terms: List<&2,C.Term>, parameters: List<&2,C.Parameter>, first: U32}
  Arms{terms: List<&2,C.Term>, source: U32}
  Arm{fields: List<&2,C.Binding>, body: C.Term, source: U32}
type Address is Data:
  Address{label: U32, pc: U32}

def internal(-A: Type, code: String) -> Result<S.Error,A>:
  Fail{S.Internal{"records",code}}
def unsupported(-A: Type, code: String) -> Result<S.Error,A>:
  Fail{S.Unsupported{"records",code,S.At{0,0,0,0}}}
def exhausted(-A: Type) -> Result<S.Error,A>:
  Fail{S.Exhausted{"records",S.At{0,0,0,0}}}
def host(-A: Type, code: String) -> Result<S.Error,A>:
  Fail{S.Host{"records",code}}

def maximum(+a: U32, +b: U32) -> U32:
  Bool.pick(U32,U32.is_ge(a,b),a,b)

def width(record: Record) -> U32:
  match record:
    case Op{1,a,b,c,d,e}: e
    case Op{4,a,b,c,d,e}: c
    case Op{8,a,b,c,d,e}: b
    case _: 0

def push(+record: Record, flow: Flow) -> Flow:
  match flow:
    case Flow{locals,next,Plan{code,captures,joins,labels,count,arity}}:
      Flow{locals,next,Plan{Con{record,code},captures,joins,labels,U32.add(count,1),maximum(arity,width(record))}}

def append(records: List<&2,Record>, flow: Flow) -> Flow:
  match records:
    case Nil{}: flow
    case Con{head,tail}: append(tail,push(head,flow))

def scope(locals: List<&2,Slot>, next: U32, flow: Flow) -> Flow:
  match flow:
    case Flow{old,unused,plan}: Flow{locals,next,plan}

def base(act: Activation) -> U32:
  match act:
    case Activation{i,b,e,r,x}: b

def source(slot: Slot) -> U32:
  match slot:
    case Slot{level,capture,data}: capture

def reserve(+count: U32, +base: U32, flow: Flow, next: U32 -> Flow -> Result<S.Error,Flow>) -> Result<S.Error,Flow>:
  match flow:
    case Flow{+locals,+first,+plan}:
      S.choose(Result<S.Error,Flow>,Bool.and(U32.is_le(first,U32.add(base,512)),U32.is_le(count,U32.sub(U32.add(base,512),first))),u =>
        next(first,Flow{locals,U32.add(first,count),plan}),u => exhausted(Flow))

def labels(+count: U32, flow: Flow, next: U32 -> Flow -> Result<S.Error,Flow>) -> Result<S.Error,Flow>:
  match flow:
    case Flow{locals,slot,Plan{code,captures,joins,+first,size,arity}}:
      next(first,Flow{locals,slot,Plan{code,captures,joins,U32.add(first,count),size,arity}})

def reusable(types: List<&2,C.Datatype>, +index: U32) -> Result<S.Error,Bool>:
  match types:
    case Nil{}: internal(Bool,"type-index")
    case Con{C.Datatype{token,+data,ctors},+tail}:
      S.choose(Result<S.Error,Bool>,U32.is_eq(index,0),u => Done{data},u => reusable(tail,U32.sub(index,1)))

def function_at(functions: List<&2,C.Function>, +index: U32) -> Result<S.Error,C.Function>:
  match functions:
    case Nil{}: internal(C.Function,"function-index")
    case Con{+head,+tail}:
      S.choose(Result<S.Error,C.Function>,U32.is_eq(index,0),u => Done{head},u => function_at(tail,U32.sub(index,1)))

def named(functions: List<&2,C.Function>, +name: String, +index: U32) -> Result<S.Error,U32>:
  match functions:
    case Nil{}: host(U32,"unknown-export")
    case Con{C.Function{C.Signature{token,params,result},body},+tail}:
      S.choose(Result<S.Error,U32>,String.eq(S.text(token),name),u => Done{index},u => named(tail,name,U32.add(index,1)))

def signature(function: C.Function, next: List<&2,C.Parameter> -> C.Term -> Result<S.Error,Flow>) -> Result<S.Error,Flow>:
  match function:
    case C.Function{C.Signature{token,params,result},body}: next(params,body)

def live(parameters: List<&2,C.Parameter>) -> U32:
  match parameters:
    case Nil{}: 0
    case Con{C.Parameter{token,q,typ},tail}:
      U32.add(Bool.pick(U32,U32.is_eq(q,0),0,1),live(tail))

def fields(parameters: List<&2,C.Binding>) -> U32:
  match parameters:
    case Nil{}: 0
    case Con{C.Binding{token,level,q,typ,p,k},tail}:
      U32.add(Bool.pick(U32,U32.is_eq(q,0),0,1),fields(tail))

def lookup(locals: List<&2,Slot>, +level: U32) -> Result<S.Error,Slot>:
  match locals:
    case Nil{}: internal(Slot,"missing-owner")
    case Con{+head,+tail}:
      match head:
        case Slot{id,capture,data}:
          S.choose(Result<S.Error,Slot>,U32.is_eq(id,level),u => Done{head},u => lookup(tail,level))

def remove(locals: List<&2,Slot>, +level: U32) -> List<&2,Slot>:
  match locals:
    case Nil{}: Nil{}
    case Con{+head,+tail}:
      match head:
        case Slot{id,capture,data}:
          S.choose(List<&2,Slot>,U32.is_eq(id,level),u => tail,u => Con{head,remove(tail,level)})

def transfer(retained: Bool, source: U32, destination: U32) -> Record:
  Op{Bool.pick(U32,retained,2,3),source,destination,0,0,0}

def occurrence(slot: Slot, +destination: U32, flow: Flow) -> Result<S.Error,Flow>:
  match slot flow:
    case Slot{level,source,+retained} Flow{+locals,next,plan}:
      Done{push(transfer(retained,source,destination),Flow{Bool.pick(List<&2,Slot>,retained,locals,remove(locals,level)),next,plan})}

def bind_slot(+types: List<&2,C.Datatype>, level: U32, typ: U32, quantity: U32, capture: U32, flow: Flow) -> Result<S.Error,Flow>:
  match flow:
    case Flow{locals,next,plan}:
      S.bind(Bool,Flow,reusable(types,typ),data => Done{Flow{Con{Slot{level,capture,Bool.and(data,U32.is_eq(quantity,2))},locals},next,plan}})

def bind_parameters(params: List<&2,C.Parameter>, +types: List<&2,C.Datatype>, +level: U32, +first: U32, +flow: Flow) -> Result<S.Error,Flow>:
  match params:
    case Nil{}: Done{flow}
    case Con{C.Parameter{token,+q,+typ},+tail}:
      S.choose(Result<S.Error,Flow>,U32.is_eq(q,0),u => bind_parameters(tail,types,U32.add(level,1),first,flow),u =>
        S.bind(Flow,Flow,bind_slot(types,level,typ,q,first,flow),state => bind_parameters(tail,types,U32.add(level,1),U32.add(first,1),state)))

def bind_fields(params: List<&2,C.Binding>, +types: List<&2,C.Datatype>, +first: U32, +flow: Flow) -> Result<S.Error,Flow>:
  match params:
    case Nil{}: Done{flow}
    case Con{C.Binding{token,+level,+q,+typ,p,k},+tail}:
      S.choose(Result<S.Error,Flow>,U32.is_eq(q,0),u => bind_fields(tail,types,first,flow),u =>
        S.bind(Flow,Flow,bind_slot(types,level,typ,q,first,flow),state => bind_fields(tail,types,U32.add(first,1),state)))

def release(source: U32) -> Record:
  Op{5,source,0,0,0,0}

def drops(locals: List<&2,Slot>, flow: Flow) -> Flow:
  match locals:
    case Nil{}: flow
    case Con{Slot{level,source,data},tail}: drops(tail,push(release(source),flow))

def cleanup(flow: Flow) -> Flow:
  match flow:
    case Flow{+locals,next,plan}: push(Op{6,65535,0,0,0,0},drops(locals,Flow{Nil{},next,plan}))

def delivery(join: U32, slot: U32, source: U32) -> Record:
  Op{9,join,1,slot,source,0}

def returned(exit: Exit, +source: U32, +flow: Flow) -> Flow:
  match exit:
    case Finish{}: push(Op{16,source,0,0,0,0},cleanup(flow))
    case Reply{+join,destination}:
      append([delivery(join,0,source),Op{11,join,1,destination,0,0}],cleanup(flow))

def moves(params: List<&2,C.Parameter>, +source: U32, +destination: U32, +flow: Flow) -> Flow:
  match params:
    case Nil{}: flow
    case Con{C.Parameter{token,q,typ},+tail}:
      S.choose(Flow,U32.is_eq(q,0),u => moves(tail,source,destination,flow),u =>
        moves(tail,U32.add(source,1),U32.add(destination,1),push(Op{3,source,destination,0,0,0},flow)))

# The logical slot is independent of completion order. Delivery consumes owners.
def deliveries(params: List<&2,C.Parameter>, +join: U32, +slot: U32, +source: U32, +flow: Flow) -> Flow:
  match params:
    case Nil{}: flow
    case Con{C.Parameter{token,q,typ},+tail}:
      S.choose(Flow,U32.is_eq(q,0),u => deliveries(tail,join,slot,source,flow),u =>
        push(delivery(join,slot,source),deliveries(tail,join,U32.add(slot,1),U32.add(source,1),flow)))

def live_terms(params: List<&2,C.Parameter>, terms: List<&2,C.Term>) -> List<&2,C.Term>:
  match params terms:
    case Con{C.Parameter{t,q,typ},+ps} Con{+head,+tail}:
      S.choose(List<&2,C.Term>,U32.is_eq(q,0),u => live_terms(ps,tail),u => Con{head,live_terms(ps,tail)})
    case _ _: Nil{}

def call_terms(function: C.Function, terms: List<&2,C.Term>) -> Result<S.Error,List<&2,C.Term>>:
  match function:
    case C.Function{C.Signature{t,params,r},body}: Done{live_terms(params,terms)}

def children(term: C.Term, functions: List<&2,C.Function>) -> Result<S.Error,List<&2,C.Term>>:
  match term:
    case C.Construct{t,i,g,p,args}: Done{live_terms(p,args)}
    case C.Application{t,i,r,args}: S.bind(C.Function,List<&2,C.Term>,function_at(functions,i),fun => call_terms(fun,args))
    case C.Let{t,l,0,i,value,body}: Done{[body]}
    case C.Let{t,l,q,i,value,body}: Done{[value,body]}
    case C.Case{t,l,i,arms}: Done{arms}
    case C.Branch{g,p,body}: Done{[body]}
    case C.Sequence{items}: Done{items}
    case _: Done{Nil{}}

def self_call(term: C.Term, index: U32) -> Bool:
  match term:
    case C.Application{t,i,r,args}: U32.is_eq(i,index)
    case _: False{}

def recursive(fuel: Nat, terms: List<&2,C.Term>, +index: U32, +functions: List<&2,C.Function>) -> Result<S.Error,Bool>:
  match fuel terms:
    case _ Nil{}: Done{False{}}
    case 0n _: exhausted(Bool)
    case 1n+ +n Con{+head,+tail}:
      S.choose(Result<S.Error,Bool>,self_call(head,index),u => Done{True{}},u =>
        S.bind(List<&2,C.Term>,Bool,children(head,functions),terms =>
          S.bind(Bool,Bool,recursive(n,terms,index,functions),+found =>
            S.choose(Result<S.Error,Bool>,found,u => Done{True{}},u => recursive(n,tail,index,functions)))))

def within(flow: Flow) -> Bool:
  match flow:
    case Flow{locals,next,Plan{code,captures,joins,labels,count,arity}}:
      Bool.and(U32.is_le(count,16384),Bool.and(U32.is_le(captures,32768),U32.is_le(joins,512)))

def checked(+flow: Flow) -> Result<S.Error,Flow>:
  S.choose(Result<S.Error,Flow>,within(flow),u => Done{flow},u => exhausted(Flow))

# New activations reserve their entire interval before any callee is emitted.
def activation(flow: Flow, next: U32 -> U32 -> Flow -> Result<S.Error,Flow>) -> Result<S.Error,Flow>:
  match flow:
    case Flow{locals,slot,Plan{code,+base,+join,labels,count,arity}}:
      S.choose(Result<S.Error,Flow>,Bool.and(U32.is_lt(base,32768),U32.is_le(join,510)),u =>
        next(base,join,Flow{locals,slot,Plan{code,U32.add(base,512),U32.add(join,2),labels,count,arity}}),u => exhausted(Flow))

def construct(data: Bool, destination: U32, tag: U32, first: U32, count: U32, flow: Flow) -> Result<S.Error,Flow>:
  Done{push(Op{1,destination,Bool.pick(U32,data,1,0),tag,first,count},flow)}

def result_scope(flow: Flow, next: List<&2,Slot> -> U32 -> Flow -> Result<S.Error,Flow>) -> Result<S.Error,Flow>:
  match flow:
    case Flow{+locals,+slot,plan}: next(locals,slot,Flow{locals,slot,plan})

def call_enter(+params: List<&2,C.Parameter>, types: List<&2,C.Datatype>, +base: U32, +callee: U32, +join: U32, +label: U32, first: U32, flow: Flow) -> Result<S.Error,Flow>:
  bind_parameters(params,types,0,callee,scope(Nil{},U32.add(callee,live(params)),
    append([Op{11,U32.add(join,1),1,callee,0,0},Mark{U32.add(label,2)},Op{15,label,0,0,0,0},Mark{label}],
      deliveries(params,U32.add(join,1),0,first,
        append([Op{8,join,1,U32.add(label,1),base,512},Op{8,U32.add(join,1),live(params),U32.add(label,2),0,0}],flow)))))

def call(+params: List<&2,C.Parameter>, +body: C.Term, +index: U32, +dst: U32, +base: U32, +first: U32, flow: Flow, +types: List<&2,C.Datatype>, +functions: List<&2,C.Function>, +depth: Nat, next: Activation -> Flow -> Result<S.Error,Flow>) -> Result<S.Error,Flow>:
  result_scope(flow,+saved => +slot => state =>
    activation(state,+callee => +join => state =>
      labels(3,state,+label => state =>
        S.bind(Bool,Flow,recursive(depth,[body],index,functions),rec =>
          S.bind(Flow,Flow,call_enter(params,types,base,callee,join,label,first,state),entered =>
            S.bind(Flow,Flow,next(Activation{index,callee,label,rec,Reply{join,dst}},entered),done =>
              checked(push(Mark{U32.add(label,1)},scope(saved,slot,done)))))))))

# Fuel bounds compilation depth. Back edges emit jumps; they never unfold source.
def lower(fuel: Nat, mode: Mode, +types: List<&2,C.Datatype>, +functions: List<&2,C.Function>, act: Activation, +flow: Flow) -> Result<S.Error,Flow>:
  match fuel mode act:
    case 0n _ _: exhausted(Flow)
    case 1n+ +n Expression{C.Value{t,+typ,+tag},+dst} +a:
      S.bind(Bool,Flow,reusable(types,typ),data => construct(data,dst,tag,0,0,flow))
    case 1n+ +n Expression{C.Construct{t,+typ,+tag,+params,+args},+dst} +a:
      reserve(live(params),base(a),flow,+first => state =>
        S.bind(Flow,Flow,lower(n,Arguments{args,params,first},types,functions,a,state),+done =>
          S.bind(Bool,Flow,reusable(types,typ),data => construct(data,dst,tag,first,live(params),done))))
    case 1n+ +n Expression{C.Reference{t,level,typ},+dst} +a:
      result_scope(flow,+locals => next => +state =>
        S.bind(Slot,Flow,lookup(locals,level),slot => occurrence(slot,dst,state)))
    case 1n+ +n Expression{C.Application{t,+index,r,+args},+dst} Activation{+self,+base,entry,+loop,exit}:
      S.choose(Result<S.Error,Flow>,U32.is_eq(index,self),u => unsupported(Flow,"recursive-activation"),u =>
        S.choose(Result<S.Error,Flow>,loop,u => unsupported(Flow,"dynamic-attempt"),u =>
          S.bind(C.Function,Flow,function_at(functions,index),fun => signature(fun,+params => +body =>
            reserve(live(params),base,flow,+first => state =>
              S.bind(Flow,Flow,lower(n,Arguments{args,params,first},types,functions,Activation{self,base,entry,loop,exit},state),arguments =>
                call(params,body,index,dst,base,first,arguments,types,functions,n,act => state => lower(n,Body{body},types,functions,act,state))))))))
    case 1n+ +n Expression{term,dst} a: unsupported(Flow,"expression-form")
    case 1n+ +n Body{C.Let{t,+level,+q,+typ,+value,+body}} +a:
      S.choose(Result<S.Error,Flow>,U32.is_eq(q,0),u => lower(n,Body{body},types,functions,a,flow),u =>
        reserve(1,base(a),flow,+dst => state =>
          S.bind(Flow,Flow,lower(n,Expression{value,dst},types,functions,a,state),done =>
            S.bind(Flow,Flow,bind_slot(types,level,typ,q,dst,done),bound => lower(n,Body{body},types,functions,a,bound)))))
    case 1n+ +n Body{C.Case{t,+level,r,+arms}} +a:
      result_scope(flow,+locals => +next => state =>
        S.bind(Slot,Flow,lookup(locals,level),slot =>
          lower(n,Arms{arms,source(slot)},types,functions,a,scope(remove(locals,level),next,state))))
    case 1n+ +n Body{C.Application{+t,+index,+r,+args}} Activation{+self,+base,+entry,+loop,+exit}:
      S.choose(Result<S.Error,Flow>,U32.is_eq(index,self),u =>
        S.bind(C.Function,Flow,function_at(functions,index),fun => signature(fun,+params => body =>
          reserve(live(params),base,flow,+first => state =>
            S.bind(Flow,Flow,lower(n,Arguments{args,params,first},types,functions,Activation{self,base,entry,loop,exit},state),done =>
              checked(push(Op{15,entry,0,0,0,0},moves(params,first,base,cleanup(done)))))))),u =>
        reserve(1,base,flow,+dst => state =>
          S.bind(Flow,Flow,lower(n,Expression{C.Application{t,index,r,args},dst},types,functions,Activation{self,base,entry,loop,exit},state),done => checked(returned(exit,dst,done)))))
    case 1n+ +n Body{term} Activation{i,+b,e,r,+exit}:
      reserve(1,b,flow,+dst => state =>
        S.bind(Flow,Flow,lower(n,Expression{term,dst},types,functions,Activation{i,b,e,r,exit},state),done => checked(returned(exit,dst,done))))
    case 1n+ +n Arguments{Nil{},Nil{},first} a: checked(flow)
    case 1n+ +n Arguments{Con{+head,+tail},Con{C.Parameter{t,q,typ},+params},+first} +a:
      S.choose(Result<S.Error,Flow>,U32.is_eq(q,0),u => lower(n,Arguments{tail,params,first},types,functions,a,flow),u =>
        S.bind(Flow,Flow,lower(n,Expression{head,first},types,functions,a,flow),done =>
          lower(n,Arguments{tail,params,U32.add(first,1)},types,functions,a,done)))
    case 1n+ +n Arguments{args,params,first} a: internal(Flow,"argument-arity")
    case 1n+ +n Arms{Con{C.Branch{tag,params,body},Nil{}},source} a:
      lower(n,Arm{params,body,source},types,functions,a,flow)
    case 1n+ +n Arms{Con{C.Branch{+tag,+params,+body},+tail},+source} +a:
      result_scope(flow,+locals => +slot => state =>
        labels(2,state,+label => state =>
          S.bind(Flow,Flow,lower(n,Arm{params,body,source},types,functions,a,
            append([Op{14,source,tag,label,U32.add(label,1),0},Mark{label}],state)),done =>
              lower(n,Arms{tail,source},types,functions,a,push(Mark{U32.add(label,1)},scope(locals,slot,done))))))
    case 1n+ +n Arms{arms,source} a: internal(Flow,"arm-node")
    case 1n+ +n Arm{+params,+body,+source} +a:
      reserve(fields(params),base(a),flow,+first => state =>
        S.bind(Flow,Flow,bind_fields(params,types,first,push(Op{4,source,first,fields(params),0,0},state)),bound =>
          lower(n,Body{body},types,functions,a,bound)))

# Relocation changes only code operands. Capture and logical-slot identities stay fixed.
def addresses(code: List<&2,Record>, +pc: U32) -> List<&2,Address>:
  match code:
    case Nil{}: Nil{}
    case Con{Mark{label},tail}: Con{Address{label,pc},addresses(tail,pc)}
    case Con{head,tail}: addresses(tail,U32.add(pc,1))

def address(table: List<&2,Address>, +label: U32) -> Result<S.Error,U32>:
  match table:
    case Nil{}: internal(U32,"missing-label")
    case Con{Address{id,+pc},+tail}:
      S.choose(Result<S.Error,U32>,U32.is_eq(id,label),u => Done{pc},u => address(tail,label))

def relocate(record: Record, +table: List<&2,Address>) -> Result<S.Error,Record>:
  match record:
    case Op{8,a,b,c,d,e}: S.bind(U32,Record,address(table,c),pc => Done{Op{8,a,b,pc,d,e}})
    case Op{14,a,b,c,+d,e}:
      S.bind(U32,Record,address(table,c),yes => S.bind(U32,Record,address(table,d),no => Done{Op{14,a,b,yes,no,e}}))
    case Op{15,a,b,c,d,e}: S.bind(U32,Record,address(table,a),pc => Done{Op{15,pc,b,c,d,e}})
    case +other: Done{other}

def show(record: Record) -> String:
  match record:
    case Op{op,a,b,c,d,e}:
      String.concat(["[",U32.show(op),",",U32.show(a),",",U32.show(b),",",U32.show(c),",",U32.show(d),",",U32.show(e),",0,0]"])
    case Mark{label}: ""

def rows(code: List<&2,Record>, +table: List<&2,Address>, +separator: String) -> Result<S.Error,List<&2,String>>:
  match code:
    case Nil{}: Done{Nil{}}
    case Con{Mark{label},tail}: rows(tail,table,separator)
    case Con{head,+tail}:
      S.bind(Record,List<&2,String>,relocate(head,table),item =>
        S.bind(List<&2,String>,List<&2,String>,rows(tail,table,","),rest => Done{Con{String.append(separator,show(item)),rest}}))

def bounded_bytes(+bytes: List<&2,U32>, +cap: U32) -> Result<S.Error,List<&2,U32>>:
  S.choose(Result<S.Error,List<&2,U32>>,U32.is_le(U32.from_nat(List.length(&2,U32,bytes)),cap),u => Done{bytes},u => exhausted(List<&2,U32>))

def encode(flow: Flow, +cap: U32) -> Result<S.Error,List<&2,U32>>:
  match flow:
    case Flow{locals,next,Plan{code,captures,joins,labels,count,arity}}:
      +ordered = List.reverse(&2,Record,code)
      S.bind(List<&2,String>,List<&2,U32>,rows(ordered,addresses(ordered,0),""),items =>
        bounded_bytes(W.chars(String.concat([
          "{\"version\":2,\"profile\":2,\"config\":{\"objects\":1024,\"captures\":",U32.show(captures),
          ",\"pending\":2048,\"joins\":",U32.show(joins),",\"arity\":",U32.show(arity),
          ",\"rcLimit\":65535,\"idLimit\":4294967295,\"attemptLimit\":4294967295,\"maxStorageBytes\":16777216},\"instructions\":[",String.concat(items),"]}\n"])),cap))

def enum_constructors(ctors: List<&2,C.Constructor>) -> Bool:
  match ctors:
    case Nil{}: True{}
    case Con{C.Constructor{t,Nil{}},tail}: enum_constructors(tail)
    case _: False{}

def enum_type(types: List<&2,C.Datatype>, +index: U32, +code: String) -> Result<S.Error,U32>:
  match types:
    case Nil{}: internal(U32,"type-index")
    case Con{C.Datatype{t,d,+ctors},+tail}:
      S.choose(Result<S.Error,U32>,U32.is_eq(index,0),u =>
        S.choose(Result<S.Error,U32>,enum_constructors(ctors),u => Done{U32.from_nat(List.length(&2,C.Constructor,ctors))},u => unsupported(U32,code)),u => enum_type(tail,U32.sub(index,1),code))

def inputs(params: List<&2,C.Parameter>, args: List<&2,U32>, +types: List<&2,C.Datatype>, +first: U32, +flow: Flow) -> Result<S.Error,Flow>:
  match params args:
    case Nil{} Nil{}: Done{flow}
    case Con{C.Parameter{t,0,typ},tail} +values: inputs(tail,values,types,first,flow)
    case Con{C.Parameter{t,q,+typ},+tail} Con{+tag,+values}:
      S.bind(U32,Flow,enum_type(types,typ,"entry-parameters"),count =>
        S.choose(Result<S.Error,Flow>,U32.is_lt(tag,count),u =>
          S.bind(Bool,Flow,reusable(types,typ),data =>
            S.bind(Flow,Flow,construct(data,first,tag,0,0,flow),state => inputs(tail,values,types,U32.add(first,1),state))),u => host(Flow,"argument-range")))
    case _ _: host(Flow,"argument-arity")

def entry(function: C.Function, +index: U32, args: List<&2,U32>, +types: List<&2,C.Datatype>, +functions: List<&2,C.Function>, +depth: Nat) -> Result<S.Error,Flow>:
  match function:
    case C.Function{C.Signature{t,+params,result},+body}:
      S.bind(U32,Flow,enum_type(types,result,"entry-result"),count =>
        S.bind(Flow,Flow,inputs(params,args,types,0,Flow{Nil{},live(params),Plan{Nil{},512,0,1,0,1}}),state =>
          S.bind(Flow,Flow,bind_parameters(params,types,0,0,push(Mark{0},state)),state =>
            S.bind(Bool,Flow,recursive(depth,[body],index,functions),rec =>
              lower(depth,Body{body},types,functions,Activation{index,0,0,rec,Finish{}},state)))))

def emit(book: C.Book, name: String, +args: List<&2,U32>, +depth: Nat, +cap: U32) -> Result<S.Error,List<&2,U32>>:
  match book:
    case C.Book{+types,+functions}:
      S.bind(U32,List<&2,U32>,named(functions,name,0),+index =>
        S.bind(C.Function,List<&2,U32>,function_at(functions,index),fun =>
          S.bind(Flow,List<&2,U32>,entry(fun,index,args,types,functions,depth),flow => encode(flow,cap))))

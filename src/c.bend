import Base
import 0xc409b77d3230ca33374caf6b0993f0cb/bytes.bend as B
import ./syntax.bend as S
import ./core.bend as C
import ./wasm-bytes.bend as W

type Local is Data:
  Local{level: U32, name: String, type_id: U32}
type Slot is Data:
  Slot{name: String, type_id: U32}
type Context is Data:
  Context{heap: List<&2,U32>, functions: List<&2,C.Function>, self: U32}
type Code is Data:
  Code{bytes: B.Builder, next: U32}
type Destination is Data:
  Return{}
  Save{name: String}
type Action is Data:
  Call{index: U32, destination: Destination}
  Cell{tag: U32, destination: Destination}
type Mode is Data:
  Expression{term: C.Term, destination: Destination}
  Arguments{terms: List<&2,C.Term>, parameters: List<&2,C.Parameter>, slots: List<&2,Slot>, action: Action}
  Branches{arms: List<&2,C.Term>, pointer: String, tag: String, destination: Destination}
  Unpack{fields: List<&2,C.Binding>, pointer: String, offset: U32, body: C.Term, destination: Destination}

def internal(-A: Type, code: String) -> Result<S.Error,A>:
  Fail{S.Internal{"c",code}}

def exhausted(-A: Type) -> Result<S.Error,A>:
  Fail{S.Exhausted{"emit",S.At{0,0,0,0}}}

def fielded(constructors: List<&2,C.Constructor>) -> Bool:
  match constructors:
    case Nil{}: False{}
    case Con{C.Constructor{token,Nil{}},tail}: fielded(tail)
    case Con{C.Constructor{token,Con{head,tail}},rest}: True{}

def heap_types(types: List<&2,C.Datatype>, +index: U32) -> List<&2,U32>:
  match types:
    case Nil{}: Nil{}
    case Con{C.Datatype{token,reusable,constructors},+tail}:
      S.choose(List<&2,U32>,fielded(constructors),u => Con{index,heap_types(tail,U32.add(index,1))},u => heap_types(tail,U32.add(index,1)))

def member(types: List<&2,U32>, +index: U32) -> Bool:
  match types:
    case Nil{}: False{}
    case Con{head,tail}: Bool.or(U32.is_eq(head,index),member(tail,index))

def boxed(context: Context, type_id: U32) -> Bool:
  match context:
    case Context{heap,functions,self}: member(heap,type_id)

def ctype(context: Context, type_id: U32) -> String:
  Bool.pick(String,boxed(context,type_id),"knot_slot *","uint32_t ")

def projection(context: Context, type_id: U32) -> String:
  Bool.pick(String,boxed(context,type_id),".ptr",".tag")

def variable(index: U32) -> String:
  String.append("v",U32.show(index))

def parameter(index: U32) -> String:
  String.append("p",U32.show(index))

def function_name(index: U32) -> String:
  String.append("knot_f",U32.show(index))

def text(cap: U32, value: String) -> Result<S.Error,B.Builder>:
  W.bytes(cap,W.chars(value))

def code(bytes: Result<S.Error,B.Builder>, +next: U32) -> Result<S.Error,Code>:
  S.bind(B.Builder,Code,bytes,b => Done{Code{b,next}})

def prepend(prefix: B.Builder, body: Code) -> Result<S.Error,Code>:
  match body:
    case Code{bytes,next}: code(W.join(prefix,bytes),next)

def prefixed(+cap: U32, prefix: String, body: Result<S.Error,Code>) -> Result<S.Error,Code>:
  S.bind(B.Builder,Code,text(cap,prefix),+bytes => S.bind(Code,Code,body,rest => prepend(bytes,rest)))

def after(initial: Code, next: U32 -> Result<S.Error,Code>) -> Result<S.Error,Code>:
  match initial:
    case Code{+bytes,index}: S.bind(Code,Code,next(index),rest => prepend(bytes,rest))

def deliver(destination: Destination, value: String) -> String:
  match destination:
    case Return{}: String.concat(["knot_result = ",value,"; goto knot_return;\n"])
    case Save{+name}: String.concat([name," = ",value,"; (void)",name,";\n"])

def lookup(locals: List<&2,Local>, +level: U32) -> Result<S.Error,Local>:
  match locals:
    case Nil{}: internal(Local,"missing-live-local")
    case Con{+head,+tail}:
      match head:
        case Local{id,name,type_id}:
          S.choose(Result<S.Error,Local>,U32.is_eq(id,level),u => Done{head},u => lookup(tail,level))

def signature(functions: List<&2,C.Function>, +index: U32) -> Result<S.Error,C.Signature>:
  match functions:
    case Nil{}: internal(C.Signature,"function-index")
    case Con{C.Function{+sig,body},+tail}:
      S.choose(Result<S.Error,C.Signature>,U32.is_eq(index,0),u => Done{sig},u => signature(tail,U32.sub(index,1)))

def callee(context: Context, index: U32) -> Result<S.Error,C.Signature>:
  match context:
    case Context{heap,functions,self}: signature(functions,index)

def parameters(params: List<&2,C.Parameter>, +level: U32) -> List<&2,Local>:
  match params:
    case Nil{}: Nil{}
    case Con{C.Parameter{token,q,+type_id},+tail}:
      S.choose(List<&2,Local>,U32.is_eq(q,0),u => parameters(tail,U32.add(level,1)),u =>
        Con{Local{level,parameter(level),type_id},parameters(tail,U32.add(level,1))})

def actuals(slots: List<&2,Slot>) -> String:
  match slots:
    case Nil{}: ""
    case Con{Slot{name,type_id},Nil{}}: name
    case Con{Slot{name,type_id},tail}: String.concat([name,",",actuals(tail)])

def stores(slots: List<&2,Slot>, +pointer: String, +offset: U32, +context: Context) -> String:
  match slots:
    case Nil{}: ""
    case Con{Slot{name,type_id},tail}:
      String.concat([pointer,"[",U32.show(offset),"]",projection(context,type_id)," = ",name,";\n",stores(tail,pointer,U32.add(offset,1),context)])

def allocate(+slots: List<&2,Slot>, tag: U32, destination: Destination, +context: Context, +next: U32, +cap: U32) -> Result<S.Error,Code>:
  S.choose(Result<S.Error,Code>,U32.is_lt(next,4096),u =>
    code(text(cap,String.concat(["knot_slot *",variable(next)," = knot_alloc(",U32.show(U32.add(1,U32.from_nat(List.length(&2,Slot,slots)))),
      ");\n",variable(next),"[0].tag = ",U32.show(tag),";\n",stores(slots,variable(next),1,context),deliver(destination,variable(next))])),U32.add(next,1)),u => exhausted(Code))

def tail_call(destination: Destination, context: Context, index: U32) -> Bool:
  match destination context:
    case Return{} Context{heap,functions,self}: U32.is_eq(index,self)
    case Save{name} context: False{}

# Every argument is saved before any parameter changes, including permutations.
def live_rebind(slots: List<&2,Slot>, +level: U32, next: List<&2,Slot> -> Result<S.Error,String>) -> Result<S.Error,String>:
  match slots:
    case Nil{}: internal(String,"tail-arity")
    case Con{Slot{+name,type_id},tail}:
      S.bind(String,String,next(tail),rest => Done{String.concat([parameter(level)," = ",name,";\n",rest])})

def rebind(params: List<&2,C.Parameter>, +slots: List<&2,Slot>, +level: U32) -> Result<S.Error,String>:
  match params:
    case Nil{}:
      match slots:
        case Nil{}: Done{"goto knot_tail;\n"}
        case Con{head,tail}: internal(String,"tail-arity")
    case Con{C.Parameter{token,q,type_id},+tail}:
      S.choose(Result<S.Error,String>,U32.is_eq(q,0),u => rebind(tail,slots,U32.add(level,1)),u =>
        live_rebind(slots,level,rest => rebind(tail,rest,U32.add(level,1))))

def rebound(sig: C.Signature, slots: List<&2,Slot>, +cap: U32, +next: U32) -> Result<S.Error,Code>:
  match sig:
    case C.Signature{token,params,result}: S.bind(String,Code,rebind(params,slots,0),s => code(text(cap,s),next))

def applied(action: Action, +slots: List<&2,Slot>, +context: Context, +next: U32, +cap: U32) -> Result<S.Error,Code>:
  match action:
    case Cell{tag,destination}: allocate(slots,tag,destination,context,next,cap)
    case Call{+index,+destination}:
      S.choose(Result<S.Error,Code>,tail_call(destination,context,index),u =>
        S.bind(C.Signature,Code,callee(context,index),sig => rebound(sig,slots,cap,next)),u =>
        code(text(cap,deliver(destination,String.concat([function_name(index),"(",actuals(slots),")"]))),next))

def declared(context: Context, type_id: U32, next: U32) -> String:
  String.concat([ctype(context,type_id),variable(next),";\n"])

def referenced(local: Local, destination: Destination, +cap: U32, next: U32) -> Result<S.Error,Code>:
  match local:
    case Local{level,name,type_id}: code(text(cap,deliver(destination,name)),next)

def call_parameters(sig: C.Signature, next: List<&2,C.Parameter> -> Result<S.Error,Code>) -> Result<S.Error,Code>:
  match sig:
    case C.Signature{token,params,result}: next(params)

def matched(local: Local, +context: Context, next: String -> String -> Result<S.Error,Code>) -> Result<S.Error,Code>:
  match local:
    case Local{level,+name,type_id}: next(name,String.append(name,Bool.pick(String,boxed(context,type_id),"[0].tag","")))

def branch_code(left: Code, right: Code, tag: U32, value: String, +cap: U32) -> Result<S.Error,Code>:
  match left right:
    case Code{a,+n} Code{b,+m}:
      code(W.concat(cap,[text(cap,String.concat(["if (",value," == ",U32.show(tag),") {\n"])),Done{a},text(cap,"} else {\n"),Done{b},text(cap,"}\n")]),Bool.pick(U32,U32.is_ge(n,m),n,m))

# Destinations separate value production from control. Only Return may loop;
# Save always computes a value, so non-tail self-calls retain their continuation.
def lower(fuel: Nat, mode: Mode, +context: Context, +locals: List<&2,Local>, +next: U32, +cap: U32) -> Result<S.Error,Code>:
  match fuel mode:
    case 0n _: exhausted(Code)
    case 1n+ +n Expression{C.Value{token,+type_id,+tag},+destination}:
      S.choose(Result<S.Error,Code>,boxed(context,type_id),u => allocate(Nil{},tag,destination,context,next,cap),u => code(text(cap,deliver(destination,U32.show(tag))),next))
    case 1n+ +n Expression{C.Construct{token,type_id,tag,params,args},destination}:
      lower(n,Arguments{args,params,Nil{},Cell{tag,destination}},context,locals,next,cap)
    case 1n+ +n Expression{C.Reference{token,level,type_id},destination}:
      S.bind(Local,Code,lookup(locals,level),local => referenced(local,destination,cap,next))
    case 1n+ +n Expression{C.Application{token,+index,type_id,+args},+destination}:
      S.bind(C.Signature,Code,callee(context,index),sig => call_parameters(sig,params =>
        lower(n,Arguments{args,params,Nil{},Call{index,destination}},context,locals,next,cap)))
    case 1n+ +n Expression{C.Let{token,+level,q,+type_id,+value,+body},+destination}:
      S.choose(Result<S.Error,Code>,U32.is_eq(q,0),u => lower(n,Expression{body,destination},context,locals,next,cap),u =>
        S.choose(Result<S.Error,Code>,U32.is_lt(next,4096),u =>
          prefixed(cap,declared(context,type_id,next),S.bind(Code,Code,lower(n,Expression{value,Save{variable(next)}},context,locals,U32.add(next,1),cap),initial =>
            after(initial,index => lower(n,Expression{body,destination},context,Con{Local{level,variable(next),type_id},locals},index,cap)))),u => exhausted(Code)))
    case 1n+ +n Expression{C.Case{token,level,type_id,+arms},+destination}:
      S.bind(Local,Code,lookup(locals,level),local => matched(local,context,pointer => tag =>
        lower(n,Branches{arms,pointer,tag,destination},context,locals,next,cap)))
    case 1n+ +n Expression{term,destination}: internal(Code,"expression-node")
    case 1n+ +n Arguments{Nil{},Nil{},slots,action}:
      applied(action,List.reverse(&2,Slot,slots),context,next,cap)
    case 1n+ +n Arguments{Con{+head,+tail},Con{C.Parameter{token,q,+type_id},+params},+slots,+action}:
      S.choose(Result<S.Error,Code>,U32.is_eq(q,0),u => lower(n,Arguments{tail,params,slots,action},context,locals,next,cap),u =>
        S.choose(Result<S.Error,Code>,U32.is_lt(next,4096),u =>
          prefixed(cap,declared(context,type_id,next),S.bind(Code,Code,lower(n,Expression{head,Save{variable(next)}},context,locals,U32.add(next,1),cap),initial =>
            after(initial,index => lower(n,Arguments{tail,params,Con{Slot{variable(next),type_id},slots},action},context,locals,index,cap)))),u => exhausted(Code)))
    case 1n+ +n Arguments{terms,params,slots,action}: internal(Code,"argument-arity")
    case 1n+ +n Branches{Con{C.Branch{tag,fields,body},Nil{}},pointer,value,destination}:
      lower(n,Unpack{fields,pointer,1,body,destination},context,locals,next,cap)
    case 1n+ +n Branches{Con{C.Branch{+tag,fields,body},+tail},+pointer,+value,+destination}:
      S.bind(Code,Code,lower(n,Unpack{fields,pointer,1,body,destination},context,locals,next,cap),left =>
        S.bind(Code,Code,lower(n,Branches{tail,pointer,value,destination},context,locals,next,cap),right => branch_code(left,right,tag,value,cap)))
    case 1n+ +n Branches{arms,pointer,value,destination}: internal(Code,"arm-node")
    case 1n+ +n Unpack{Nil{},pointer,offset,body,destination}: lower(n,Expression{body,destination},context,locals,next,cap)
    case 1n+ +n Unpack{Con{C.Binding{token,+level,q,+type_id,param,known},+tail},+pointer,+offset,+body,+destination}:
      S.choose(Result<S.Error,Code>,U32.is_eq(q,0),u => lower(n,Unpack{tail,pointer,offset,body,destination},context,locals,next,cap),u =>
        S.choose(Result<S.Error,Code>,U32.is_lt(next,4096),u =>
          prefixed(cap,String.concat([declared(context,type_id,next),deliver(Save{variable(next)},String.concat([pointer,"[",U32.show(offset),"]",projection(context,type_id)]))]),
            lower(n,Unpack{tail,pointer,U32.add(offset,1),body,destination},context,Con{Local{level,variable(next),type_id},locals},U32.add(next,1),cap)),u => exhausted(Code)))

def formal_list(locals: List<&2,Local>, +context: Context) -> String:
  match locals:
    case Nil{}: ""
    case Con{Local{level,name,type_id},Nil{}}: String.append(ctype(context,type_id),name)
    case Con{Local{level,name,type_id},tail}: String.concat([ctype(context,type_id),name,",",formal_list(tail,context)])

def formals(locals: List<&2,Local>, context: Context) -> String:
  match locals:
    case Nil{}: "void"
    case Con{+head,+tail}: formal_list(Con{head,tail},context)

def ignored(locals: List<&2,Local>) -> String:
  match locals:
    case Nil{}: ""
    case Con{Local{level,name,type_id},tail}: String.concat(["(void)",name,";\n",ignored(tail)])

def prototype(sig: C.Signature, name: String, +context: Context) -> String:
  match sig:
    case C.Signature{token,params,result}:
      String.concat([ctype(context,result),name,"(",formals(parameters(params,0),context),")"])

def definition(body: Code, +sig: C.Signature, +index: U32, +context: Context, +cap: U32) -> Result<S.Error,B.Builder>:
  match body sig:
    case Code{bytes,+next} C.Signature{token,+params,+result}:
      +locals = parameters(params,0)
      W.concat(cap,[text(cap,String.concat([prototype(sig,function_name(index),context)," {\n",ctype(context,result),"knot_result = 0;\n",
        "const size_t knot_frame = ",U32.show(U32.add(64,U32.mul(32,U32.add(next,U32.from_nat(List.length(&2,Local,locals)))))),";\nknot_enter(knot_frame);\n",ignored(locals),
        "if (0) goto knot_return;\ngoto knot_tail;\nknot_tail:;\n"])),Done{bytes},text(cap,"knot_return:\nknot_leave(knot_frame);\nreturn knot_result;\n}\n")])

def definitions(remaining: List<&2,C.Function>, +index: U32, +heap: List<&2,U32>, +all: List<&2,C.Function>, +depth: Nat, +cap: U32) -> Result<S.Error,B.Builder>:
  match remaining:
    case Nil{}: Done{B.empty(cap)}
    case Con{C.Function{+sig,body},+tail}:
      match sig:
        case C.Signature{token,params,result}:
          +context : Context = Context{heap,all,index}
          S.bind(Code,B.Builder,lower(depth,Expression{body,Return{}},context,parameters(params,0),0,cap),code =>
            W.concat(cap,[definition(code,sig,index,context,cap),definitions(tail,U32.add(index,1),heap,all,depth,cap)]))

def prototypes(functions: List<&2,C.Function>, +index: U32, +context: Context, +cap: U32) -> Result<S.Error,B.Builder>:
  match functions:
    case Nil{}: Done{B.empty(cap)}
    case Con{C.Function{sig,body},tail}:
      W.concat(cap,[text(cap,String.append(prototype(sig,function_name(index),context),";\n")),prototypes(tail,U32.add(index,1),context,cap)])

def enum_parameters(params: List<&2,C.Parameter>, +context: Context) -> Bool:
  match params:
    case Nil{}: True{}
    case Con{C.Parameter{token,q,type_id},tail}:
      Bool.and(Bool.or(U32.is_eq(q,0),Bool.not(boxed(context,type_id))),enum_parameters(tail,context))

def exported(sig: C.Signature, +context: Context) -> Bool:
  match sig:
    case C.Signature{token,params,result}: Bool.and(Bool.not(boxed(context,result)),enum_parameters(params,context))

def ordinal_count(types: List<&2,C.Datatype>, +index: U32) -> U32:
  match types:
    case Nil{}: 0
    case Con{C.Datatype{token,reusable,constructors},+tail}:
      S.choose(U32,U32.is_eq(index,0),u => U32.from_nat(List.length(&2,C.Constructor,constructors)),u => ordinal_count(tail,U32.sub(index,1)))

def domains(locals: List<&2,Local>, +types: List<&2,C.Datatype>) -> String:
  match locals:
    case Nil{}: ""
    case Con{Local{level,name,type_id},tail}:
      String.concat(["if (",name," >= ",U32.show(ordinal_count(types,type_id)),") knot_fail(5,\"HostFailure\\tc\\tordinal-domain\");\n",domains(tail,types)])

def local_slots(locals: List<&2,Local>) -> List<&2,Slot>:
  match locals:
    case Nil{}: Nil{}
    case Con{Local{level,name,type_id},tail}: Con{Slot{name,type_id},local_slots(tail)}

def export_name(index: U32) -> String:
  String.append("knot_export_",U32.show(index))

def wrapper(sig: C.Signature, +index: U32, +types: List<&2,C.Datatype>, +context: Context) -> String:
  match sig:
    case C.Signature{token,+params,result}:
      +locals = parameters(params,0)
      String.concat([prototype(sig,export_name(index),context)," {\n",domains(locals,types),"return ",function_name(index),"(",actuals(local_slots(locals)),");\n}\n"])

def wrappers(functions: List<&2,C.Function>, +index: U32, +types: List<&2,C.Datatype>, +context: Context, +cap: U32) -> Result<S.Error,B.Builder>:
  match functions:
    case Nil{}: Done{B.empty(cap)}
    case Con{C.Function{+sig,body},+tail}:
      W.concat(cap,[S.choose(Result<S.Error,B.Builder>,exported(sig,context),u => text(cap,wrapper(sig,index,types,context)),u => Done{B.empty(cap)}),
        wrappers(tail,U32.add(index,1),types,context,cap)])

def host_actuals(locals: List<&2,Local>, +index: U32) -> String:
  match locals:
    case Nil{}: ""
    case Con{head,Nil{}}: String.concat(["args[",U32.show(index),"]"])
    case Con{head,tail}: String.concat(["args[",U32.show(index),"],",host_actuals(tail,U32.add(index,1))])

def dispatch(sig: C.Signature, +index: U32) -> String:
  match sig:
    case C.Signature{token,+params,result}:
      +locals = parameters(params,0)
      String.concat(["if (strcmp(name,\"",S.text(token),"\") == 0) {\nif (argc != ",U32.show(U32.from_nat(List.length(&2,Local,locals))),
        ") knot_fail(5,\"HostFailure\\tc\\tarity\");\nreturn ",export_name(index),"(",host_actuals(locals,0),");\n}\n"])

def dispatches(functions: List<&2,C.Function>, +index: U32, +context: Context, +cap: U32) -> Result<S.Error,B.Builder>:
  match functions:
    case Nil{}: Done{B.empty(cap)}
    case Con{C.Function{+sig,body},+tail}:
      W.concat(cap,[S.choose(Result<S.Error,B.Builder>,exported(sig,context),u => text(cap,dispatch(sig,index)),u => Done{B.empty(cap)}),
        dispatches(tail,U32.add(index,1),context,cap)])

def runtime() -> String:
  "#include <stdint.h>\n#include <stddef.h>\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#ifndef KNOT_ARENA_SLOTS\n#define KNOT_ARENA_SLOTS 16384u\n#endif\n#ifndef KNOT_DEPTH_LIMIT\n#define KNOT_DEPTH_LIMIT 256u\n#endif\n#ifndef KNOT_STACK_BYTES\n#define KNOT_STACK_BYTES 1048576u\n#endif\n#ifndef KNOT_SOURCE_BYTES\n#define KNOT_SOURCE_BYTES 0u\n#endif\ntypedef union knot_slot knot_slot;\nunion knot_slot { uint32_t tag; knot_slot *ptr; };\nstatic knot_slot knot_arena[KNOT_ARENA_SLOTS];\nstatic size_t knot_bump, knot_depth, knot_stack;\nvoid knot_fail(int status, const char *message) {\n  fprintf(stderr,\"%s\\n\",message);\n  exit(status);\n}\nvoid knot_reset(void) { knot_bump = knot_depth = knot_stack = 0; }\nknot_slot *knot_alloc(size_t size) {\n  if (size > KNOT_ARENA_SLOTS - knot_bump)\n    knot_fail(4,\"Exhausted\\tc\\tarena-overflow\");\n  knot_slot *cell = knot_arena + knot_bump;\n  knot_bump += size;\n  return cell;\n}\nvoid knot_enter(size_t frame) {\n  if (knot_depth >= KNOT_DEPTH_LIMIT || frame > KNOT_STACK_BYTES - knot_stack)\n    knot_fail(4,\"Exhausted\\tc\\tcall-stack\");\n  knot_depth++;\n  knot_stack += frame;\n}\nvoid knot_leave(size_t frame) { knot_depth--; knot_stack -= frame; }\n"

def shim() -> String:
  "#ifndef KNOT_NO_MAIN\nint main(int argc, char **argv) {\n  uint32_t args[256];\n  if (argc < 2 || argc > 258) knot_fail(5,\"HostFailure\\tc\\targuments\");\n  for (int i = 2; i < argc; i++) {\n    const char *s = argv[i];\n    uint32_t value = 0;\n    if (!*s || (*s == '0' && s[1])) knot_fail(5,\"HostFailure\\tc\\tordinal\");\n    for (; *s; s++) {\n      if (*s < '0' || *s > '9' || value > 25u || (value == 25u && *s > '5'))\n        knot_fail(5,\"HostFailure\\tc\\tordinal\");\n      value = value * 10u + (uint32_t)(*s - '0');\n    }\n    args[i-2] = value;\n  }\n  knot_reset();\n  uint32_t result = knot_invoke(argv[1],(size_t)(argc-2),args);\n  printf(\"{\\\"validated\\\":true,\\\"export\\\":\\\"%s\\\",\\\"arguments\\\":[\",argv[1]);\n  for (int i = 2; i < argc; i++) printf(\"%s%u\",i == 2 ? \"\" : \",\",(unsigned)args[i-2]);\n  printf(\"],\\\"result\\\":%u,\\\"bytes\\\":%u}\\n\",(unsigned)result,(unsigned)KNOT_SOURCE_BYTES);\n  return 0;\n}\n#endif\n"

# The driver establishes complete checking before this entry. Every emitted
# fragment is bounded by the byte builder before the output file is opened.
def emit(book: C.Book, +depth: Nat, +cap: U32) -> Result<S.Error,List<&2,U32>>:
  match book:
    case C.Book{+types,+functions}:
      +heap = heap_types(types,0)
      +context : Context = Context{heap,functions,0}
      S.bind(B.Builder,List<&2,U32>,W.concat(cap,[text(cap,runtime()),prototypes(functions,0,context,cap),definitions(functions,0,heap,functions,depth,cap),
        wrappers(functions,0,types,context,cap),text(cap,"uint32_t knot_invoke(const char *name, size_t argc, const uint32_t *args) {\nif (!name || (argc && !args)) knot_fail(5,\"HostFailure\\tc\\targuments\");\n(void)argc; (void)args;\n"),
        dispatches(functions,0,context,cap),text(cap,"knot_fail(5,\"HostFailure\\tc\\tunknown-export\");\nreturn 0;\n}\n"),text(cap,shim())]),bytes => Done{B.finish(bytes)})

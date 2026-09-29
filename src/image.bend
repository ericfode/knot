import Base
import ./syntax.bend as S
import ./core.bend as C

# knot-image-1 (vm/SPEC.md). A checked Book is erased to a Plan, the image's own tree of records,
# and a Plan is laid out as little-endian 32-bit words. `erase_tokens` is the first step, `layout`
# the second, and `decode` inverts the second, so decode(layout(p)) = p on every plan `layout`
# accepts. The three pass through no unchecked node: a form without an encoding is reported
# `Unsupported compile image-term`, a broken invariant `InternalFailure compile`.

def none() -> U32:
  4294967295

type Constant is Data:
  Constant{kind: U32, data: List<&2,U32>}

type Constructor is Data:
  Constructor{name: String, fields: List<&2,U32>}

# Kinds 0..3 of SPEC section 2. A field, domain or result of `none()` is an erased position.
type Shape is Data:
  Algebraic{name: String, constructors: List<&2,Constructor>}
  Arrow{domain: U32, result: U32}
  Erased{domain: U32, result: U32}
  Opaque{name: String}

# One record per core form (SPEC section 3). Every node carries its result type. A Case holds one
# row per constructor, in tag order (mode 0), or one per key (mode 1).
type Node is Data:
  Literal{type_id: U32, constant: Constant}
  Intrinsic{type_id: U32, prim: U32, operands: List<&2,Node>}
  Value{type_id: U32, tag: U32}
  Construct{type_id: U32, tag: U32, operands: List<&2,Node>}
  Reference{type_id: U32, slot: U32}
  Application{type_id: U32, function: U32, operands: List<&2,Node>}
  Let{type_id: U32, slot: U32, value: Node, body: Node}
  Case{type_id: U32, slot: U32, scrutinee: U32, mode: U32, rows: List<&2,Row>, default: Maybe<&2,Node>}
  Closure{type_id: U32, live: U32, slots: U32, captures: List<&2,U32>, body: Node}
  Invoke{type_id: U32, function: Node, arguments: List<&2,Node>}
  Foreign{type_id: U32, foreign: U32, operands: List<&2,Node>}
type Row is Data:
  Missing{}
  Branch{key: U32, first: U32, fields: U32, body: Node}

type Function is Data:
  Function{name: String, parameters: List<&2,U32>, result: U32, slots: U32, body: Node}
type Plan is Data:
  Plan{entry: U32, representation: List<&2,U32>, shapes: List<&2,Shape>, functions: List<&2,Function>}

def diagnostic(-A: Type, code: String) -> Result<S.Error,A>:
  Fail{S.Internal{"compile",code}}

def unsupported(-A: Type, code: String) -> Result<S.Error,A>:
  Fail{S.Unsupported{"compile",code,S.At{0,0,0,0}}}

def type_of(node: Node) -> U32:
  match node:
    case Literal{type_id,constant}: type_id
    case Intrinsic{type_id,prim,operands}: type_id
    case Value{type_id,tag}: type_id
    case Construct{type_id,tag,operands}: type_id
    case Reference{type_id,slot}: type_id
    case Application{type_id,function,operands}: type_id
    case Let{type_id,slot,value,body}: type_id
    case Case{type_id,slot,scrutinee,mode,rows,default}: type_id
    case Closure{type_id,live,slots,captures,body}: type_id
    case Invoke{type_id,function,arguments}: type_id
    case Foreign{type_id,foreign,operands}: type_id

# ---------------------------------------------------------------- erasure

# A level is a binder of the checked core; a slot is its place among the live binders. An erased
# binder has no slot, and a live reference to it is an invariant break, not source Invalid.
type Local is Data:
  Local{level: U32, slot: U32, type_id: U32, live: Bool}

type Bound is Data:
  Bound{locals: List<&2,Local>, depth: U32}

type Lowered is Data:
  Lowered{nodes: List<&2,Node>, rows: List<&2,Row>, deepest: U32}

# Term is one node, Operands the live ones among a call's or constructor's, Table one row per
# constructor of the scrutinee's type, Arm the row of one tag. Bind, Scrutinee and Fields hold a
# value that the next step inspects: a match reads a def's parameter, never a computed value.
type Mode is Data:
  Term{term: C.Term}
  Operands{terms: List<&2,C.Term>, parameters: List<&2,C.Parameter>}
  Table{arms: List<&2,C.Term>, tag: U32, constructors: List<&2,C.Constructor>}
  Arm{arm: Maybe<&2,C.Term>, key: U32}
  Bind{value: Lowered, level: U32, body: C.Term}
  Scrutinee{local: Local, type_id: U32, arms: List<&2,C.Term>}
  Fields{bound: Bound, body: C.Term, key: U32, count: U32}

def live_types(parameters: List<&2,C.Parameter>) -> List<&2,U32>:
  match parameters:
    case Nil{}: Nil{}
    case Con{C.Parameter{token,+q,+type_id},+tail}:
      S.choose(List<&2,U32>,U32.is_eq(q,0),u => live_types(tail),u => Con{type_id,live_types(tail)})

def live_count(parameters: List<&2,C.Parameter>) -> U32:
  match parameters:
    case Nil{}: 0
    case Con{C.Parameter{token,+q,type_id},+tail}:
      S.choose(U32,U32.is_eq(q,0),u => live_count(tail),u => U32.add(1,live_count(tail)))

def live_bindings(bindings: List<&2,C.Binding>) -> U32:
  match bindings:
    case Nil{}: 0
    case Con{C.Binding{token,level,+q,type_id,parameter,known},+tail}:
      S.choose(U32,U32.is_eq(q,0),u => live_bindings(tail),u => U32.add(1,live_bindings(tail)))

def parameter_locals(parameters: List<&2,C.Parameter>, +level: U32, +depth: U32, +locals: List<&2,Local>) -> Bound:
  match parameters:
    case Nil{}: Bound{locals,depth}
    case Con{C.Parameter{token,q,+type_id},+tail}:
      S.choose(Bound,U32.is_eq(q,0),u =>
        parameter_locals(tail,U32.add(level,1),depth,Con{Local{level,0,type_id,False{}},locals}),u =>
        parameter_locals(tail,U32.add(level,1),U32.add(depth,1),Con{Local{level,depth,type_id,True{}},locals}))

def field_locals(bindings: List<&2,C.Binding>, +depth: U32, +locals: List<&2,Local>) -> Bound:
  match bindings:
    case Nil{}: Bound{locals,depth}
    case Con{C.Binding{token,+level,q,+type_id,parameter,known},+tail}:
      S.choose(Bound,U32.is_eq(q,0),u =>
        field_locals(tail,depth,Con{Local{level,0,type_id,False{}},locals}),u =>
        field_locals(tail,U32.add(depth,1),Con{Local{level,depth,type_id,True{}},locals}))

def lookup(locals: List<&2,Local>, +level: U32) -> Result<S.Error,Local>:
  match locals:
    case Nil{}: diagnostic(Local,"image-level")
    case Con{+head,+tail}:
      match head:
        case Local{id,slot,type_id,live}:
          S.choose(Result<S.Error,Local>,U32.is_eq(id,level),u => Done{head},u => lookup(tail,level))

def live_local(local: Local) -> Result<S.Error,Local>:
  match local:
    case Local{level,slot,type_id,+live}:
      S.choose(Result<S.Error,Local>,live,u => Done{Local{level,slot,type_id,live}},u => diagnostic(Local,"image-erased-reference"))

def function_at(functions: List<&2,C.Function>, +index: U32) -> Result<S.Error,C.Function>:
  match functions:
    case Nil{}: diagnostic(C.Function,"image-function")
    case Con{+head,+tail}:
      S.choose(Result<S.Error,C.Function>,U32.is_eq(index,0),u => Done{head},u => function_at(tail,U32.sub(index,1)))

def datatype_at(types: List<&2,C.Datatype>, +index: U32) -> Result<S.Error,C.Datatype>:
  match types:
    case Nil{}: diagnostic(C.Datatype,"image-type")
    case Con{+head,+tail}:
      S.choose(Result<S.Error,C.Datatype>,U32.is_eq(index,0),u => Done{head},u => datatype_at(tail,U32.sub(index,1)))

def signature_parameters(function: C.Function) -> List<&2,C.Parameter>:
  match function:
    case C.Function{C.Signature{token,parameters,result},body}: parameters

def datatype_constructors(definition: C.Datatype) -> List<&2,C.Constructor>:
  match definition:
    case C.Datatype{token,reusable,constructors}: constructors

# The arm of a tag, if the source has one: on the current base a checked Case is exhaustive.
def arm_for(arms: List<&2,C.Term>, +tag: U32) -> Maybe<&2,C.Term>:
  match arms:
    case Nil{}: None{}
    case Con{+head,+tail}:
      match head:
        case C.Branch{pattern,fields,body}:
          S.choose(Maybe<&2,C.Term>,U32.is_eq(pattern,tag),u => Some{head},u => arm_for(tail,tag))
        case _: None{}

def max_depth(+a: U32, +b: U32) -> U32:
  Bool.pick(U32,U32.is_ge(a,b),a,b)

def single(lowered: Lowered) -> Result<S.Error,Lowered>:
  match lowered:
    case Lowered{Con{node,Nil{}},rows,deepest}: Done{lowered}
    case _: diagnostic(Lowered,"image-single")

def joined(head: Lowered, tail: Lowered) -> Result<S.Error,Lowered>:
  match head tail:
    case Lowered{Con{node,Nil{}},Nil{},+a} Lowered{nodes,rows,+b}: Done{Lowered{Con{node,nodes},rows,max_depth(a,b)}}
    case _ _: diagnostic(Lowered,"image-operand")

def prepend_row(head: Lowered, tail: Lowered) -> Result<S.Error,Lowered>:
  match head tail:
    case Lowered{Nil{},Con{row,Nil{}},+a} Lowered{nodes,rows,+b}: Done{Lowered{nodes,Con{row,rows},max_depth(a,b)}}
    case _ _: diagnostic(Lowered,"image-row")

def one(node: Node, deepest: U32) -> Lowered:
  Lowered{Con{node,Nil{}},Nil{},deepest}

# A constructor whose fields are all erased has no operand: the image spells it as a Value.
def constructed(operands: Lowered, +type_id: U32, +tag: U32) -> Result<S.Error,Lowered>:
  match operands:
    case Lowered{Nil{},rows,deepest}: Done{one(Value{type_id,tag},deepest)}
    case Lowered{nodes,rows,deepest}: Done{one(Construct{type_id,tag,nodes},deepest)}

def called(operands: Lowered, +type_id: U32, +index: U32) -> Result<S.Error,Lowered>:
  match operands:
    case Lowered{nodes,rows,deepest}: Done{one(Application{type_id,index,nodes},deepest)}

def referenced(local: Local, +depth: U32) -> Result<S.Error,Lowered>:
  match local:
    case Local{level,slot,type_id,live}: Done{one(Reference{type_id,slot},depth)}

# The Let's own type is its body's: a positional type, never the initializer's (SPEC section 3).
def bound_let(value: Lowered, body: Lowered, +slot: U32) -> Result<S.Error,Lowered>:
  match value body:
    case Lowered{Con{initial,Nil{}},Nil{},+a} Lowered{Con{+result,Nil{}},Nil{},+b}:
      Done{one(Let{type_of(result),slot,initial,result},max_depth(a,b))}
    case _ _: diagnostic(Lowered,"image-let")

def case_node(table: Lowered, +type_id: U32, +slot: U32, +scrutinee: U32) -> Result<S.Error,Lowered>:
  match table:
    case Lowered{Nil{},rows,deepest}: Done{one(Case{type_id,slot,scrutinee,0,rows,None{}},deepest)}
    case _: diagnostic(Lowered,"image-case")

def branch_row(body: Lowered, +key: U32, +first: U32, +fields: U32) -> Result<S.Error,Lowered>:
  match body:
    case Lowered{Con{node,Nil{}},Nil{},deepest}: Done{Lowered{Nil{},Con{Branch{key,first,fields,node},Nil{}},deepest}}
    case _: diagnostic(Lowered,"image-branch")

# The current base has no term that needs a wider encoding; each form below is exhaustive so that a
# new C.Term constructor cannot compile until it is encoded or refused here.
def lower(fuel: Nat, mode: Mode, +types: List<&2,C.Datatype>, +functions: List<&2,C.Function>, +locals: List<&2,Local>, +depth: U32) -> Result<S.Error,Lowered>:
  match fuel mode:
    case 0n _: Fail{S.Exhausted{"compile",S.At{0,0,0,0}}}
    case 1n+ +n Term{C.Value{token,+type_id,+tag}}: Done{one(Value{type_id,tag},depth)}
    case 1n+ +n Term{C.Construct{token,+type_id,+tag,+fields,+arguments}}:
      S.bind(Lowered,Lowered,lower(n,Operands{arguments,fields},types,functions,locals,depth),operands => constructed(operands,type_id,tag))
    case 1n+ +n Term{C.Reference{token,+level,type_id}}:
      S.bind(Local,Lowered,lookup(locals,level),found =>
        S.bind(Local,Lowered,live_local(found),local => referenced(local,depth)))
    case 1n+ +n Term{C.Application{token,+index,+type_id,+arguments}}:
      S.bind(C.Function,Lowered,function_at(functions,index),callee =>
        S.bind(Lowered,Lowered,lower(n,Operands{arguments,signature_parameters(callee)},types,functions,locals,depth),operands => called(operands,type_id,index)))
    case 1n+ +n Term{C.Let{token,+level,+q,+type_id,+value,+body}}:
      S.choose(Result<S.Error,Lowered>,U32.is_eq(q,0),u =>
        lower(n,Term{body},types,functions,Con{Local{level,0,type_id,False{}},locals},depth),u =>
        S.bind(Lowered,Lowered,lower(n,Term{value},types,functions,locals,depth),initial =>
          lower(n,Bind{initial,level,body},types,functions,locals,depth)))
    case 1n+ +n Term{C.Case{token,+level,+type_id,+arms}}:
      S.bind(Local,Lowered,lookup(locals,level),found =>
        S.bind(Local,Lowered,live_local(found),local => lower(n,Scrutinee{local,type_id,arms},types,functions,locals,depth)))
    case 1n+ +n Term{C.Branch{tag,fields,body}}: diagnostic(Lowered,"image-branch-node")
    case 1n+ +n Term{C.Sequence{items}}: diagnostic(Lowered,"image-sequence-node")
    case 1n+ +n Operands{Nil{},Nil{}}: Done{Lowered{Nil{},Nil{},depth}}
    case 1n+ +n Operands{Con{+head,+tail},Con{C.Parameter{token,+q,type_id},+rest}}:
      S.choose(Result<S.Error,Lowered>,U32.is_eq(q,0),u => lower(n,Operands{tail,rest},types,functions,locals,depth),u =>
        S.bind(Lowered,Lowered,lower(n,Term{head},types,functions,locals,depth),first =>
          S.bind(Lowered,Lowered,lower(n,Operands{tail,rest},types,functions,locals,depth),remaining => joined(first,remaining))))
    case 1n+ +n Operands{terms,parameters}: diagnostic(Lowered,"image-argument-arity")
    case 1n+ +n Table{arms,+tag,Nil{}}: Done{Lowered{Nil{},Nil{},depth}}
    case 1n+ +n Table{+arms,+tag,Con{constructor,+rest}}:
      S.bind(Lowered,Lowered,lower(n,Arm{arm_for(arms,tag),tag},types,functions,locals,depth),row =>
        S.bind(Lowered,Lowered,lower(n,Table{arms,U32.add(tag,1),rest},types,functions,locals,depth),remaining => prepend_row(row,remaining)))
    case 1n+ +n Arm{None{},key}: Done{Lowered{Nil{},Con{Missing{},Nil{}},depth}}
    case 1n+ +n Arm{Some{C.Branch{pattern,+fields,+body}},+key}:
      lower(n,Fields{field_locals(fields,depth,locals),body,key,live_bindings(fields)},types,functions,locals,depth)
    case 1n+ +n Arm{other,key}: diagnostic(Lowered,"image-arm-node")
    case 1n+ +n Bind{Lowered{Con{+node,Nil{}},Nil{},+a},+level,+body}:
      S.bind(Lowered,Lowered,lower(n,Term{body},types,functions,Con{Local{level,depth,type_of(node),True{}},locals},U32.add(depth,1)),inner =>
        bound_let(Lowered{Con{node,Nil{}},Nil{},a},inner,depth))
    case 1n+ +n Bind{value,level,body}: diagnostic(Lowered,"image-let")
    case 1n+ +n Scrutinee{Local{id,+slot,+scrutinee,live},+type_id,+arms}:
      S.bind(C.Datatype,Lowered,datatype_at(types,scrutinee),definition =>
        S.bind(Lowered,Lowered,lower(n,Table{arms,0,datatype_constructors(definition)},types,functions,locals,depth),table => case_node(table,type_id,slot,scrutinee)))
    case 1n+ +n Fields{Bound{extended,+inner},+body,+key,+count}:
      S.bind(Lowered,Lowered,lower(n,Term{body},types,functions,extended,inner),lowered =>
        branch_row(lowered,key,depth,count))

def constructor_plan(constructors: List<&2,C.Constructor>) -> List<&2,Constructor>:
  match constructors:
    case Nil{}: Nil{}
    case Con{C.Constructor{token,fields},tail}: Con{Constructor{S.text(token),live_types(fields)},constructor_plan(tail)}

def shape_plan(types: List<&2,C.Datatype>) -> List<&2,Shape>:
  match types:
    case Nil{}: Nil{}
    case Con{C.Datatype{token,reusable,constructors},tail}: Con{Algebraic{S.text(token),constructor_plan(constructors)},shape_plan(tail)}

def function_done(lowered: Lowered, +name: String, +parameters: List<&2,U32>, +result: U32) -> Result<S.Error,Function>:
  match lowered:
    case Lowered{Con{node,Nil{}},Nil{},deepest}: Done{Function{name,parameters,result,deepest,node}}
    case _: diagnostic(Function,"image-body")

def function_lowered(fuel: Nat, bound: Bound, +body: C.Term, +name: String, +live: List<&2,U32>, +result: U32, +types: List<&2,C.Datatype>, +functions: List<&2,C.Function>) -> Result<S.Error,Function>:
  match bound:
    case Bound{locals,depth}:
      S.bind(Lowered,Function,lower(fuel,Term{body},types,functions,locals,depth),lowered => function_done(lowered,name,live,result))

def function_plan(fuel: Nat, function: C.Function, +types: List<&2,C.Datatype>, +functions: List<&2,C.Function>) -> Result<S.Error,Function>:
  match function:
    case C.Function{C.Signature{token,+parameters,+result},+body}:
      function_lowered(fuel,parameter_locals(parameters,0,0,Nil{}),body,S.text(token),live_types(parameters),result,types,functions)

def function_plans(+fuel: Nat, remaining: List<&2,C.Function>, +types: List<&2,C.Datatype>, +functions: List<&2,C.Function>) -> Result<S.Error,List<&2,Function>>:
  match remaining:
    case Nil{}: Done{Nil{}}
    case Con{+head,tail}:
      S.bind(Function,List<&2,Function>,function_plan(fuel,head,types,functions),first =>
        S.bind(List<&2,Function>,List<&2,Function>,function_plans(fuel,tail,types,functions),rest => Done{Con{first,rest}}))

# Nat, U32, Char, String, Bool, Cmp, Unit, List, Result, Sigma, IO.OP and File are pinned by a Base
# import, which this base does not accept: no representation type is declared.
def undeclared() -> List<&2,U32>:
  [none(),none(),none(),none(),none(),none(),none(),none(),none(),none(),none(),none()]

# The plan of a checked book: tokens, quantity-0 binders, levels and datatype kinds do not survive.
def erase_tokens(fuel: Nat, book: C.Book) -> Result<S.Error,Plan>:
  match book:
    case C.Book{+types,+functions}:
      S.bind(List<&2,Function>,Plan,function_plans(fuel,functions,types,functions),planned => Done{Plan{0,undeclared(),shape_plan(types),planned}})

# ---------------------------------------------------------------- layout

def magic() -> U32:
  1196247371

# The pinned base.bend digest (vm/registry.json), packed little-endian: word i is bytes 4i..4i+3.
def digest() -> List<&2,U32>:
  [967372322,1597628945,3931068771,212603004,2186566430,3374278737,2120669052,453228302]

def image_words() -> U32:
  4194304

def table_records() -> U32:
  1048576

def count_onto(words: List<&2,U32>, +size: U32) -> U32:
  match words:
    case Nil{}: size
    case Con{head,tail}: count_onto(tail,U32.add(size,1))

def count(words: List<&2,U32>) -> U32:
  count_onto(words,0)

def total_onto(records: List<&2,List<&2,U32>>, +size: U32) -> U32:
  match records:
    case Nil{}: size
    case Con{head,tail}: total_onto(tail,U32.add(size,count(head)))

def total(records: List<&2,List<&2,U32>>) -> U32:
  total_onto(records,0)

def exhausted(-A: Type) -> Result<S.Error,A>:
  Fail{S.Exhausted{"compile",S.At{0,0,0,0}}}

# Names are interned in first-use order, by their exact text.
type Names is Data:
  Names{list: List<&2,String>, size: U32}
type Interned is Data:
  Interned{index: U32, names: Names}

# `top` is the index of the list's head: the list holds the newest name first.
def locate(list: List<&2,String>, +text: String, +top: U32) -> Maybe<&2,U32>:
  match list:
    case Nil{}: None{}
    case Con{+head,+tail}:
      S.choose(Maybe<&2,U32>,String.eq(head,text),u => Some{top},u => locate(tail,text,U32.sub(top,1)))

def interned_at(found: Maybe<&2,U32>, +list: List<&2,String>, +size: U32, +text: String) -> Interned:
  match found:
    case Some{index}: Interned{index,Names{list,size}}
    case None{}: Interned{size,Names{Con{text,list},U32.add(size,1)}}

def intern(names: Names, +text: String) -> Interned:
  match names:
    case Names{+list,+size}: interned_at(locate(list,text,U32.sub(size,1)),list,size,text)

# A shape's record is [length, kind, name, a, b] and a constructor's [length, type, tag, name,
# live fields, field types...]. A Records value carries its records newest first; the builders end
# with one reversal. A function's record needs its root, so its head waits for the node pass.
type Records is Data:
  Records{records: List<&2,List<&2,U32>>, names: Names, next: U32}

def shaped(named: Interned, acc: List<&2,List<&2,U32>>, +first: U32, +count: U32) -> Records:
  match named:
    case Interned{index,names}: Records{Con{[5,0,index,first,count],acc},names,U32.add(first,count)}

def opaque(named: Interned, acc: List<&2,List<&2,U32>>, first: U32) -> Records:
  match named:
    case Interned{index,names}: Records{Con{[5,3,index,0,0],acc},names,first}

def shape_row(shape: Shape, rows: Records) -> Records:
  match shape rows:
    case Algebraic{name,constructors} Records{acc,names,first}:
      shaped(intern(names,name),acc,first,U32.from_nat(List.length(&2,Constructor,constructors)))
    case Arrow{domain,result} Records{acc,names,first}: Records{Con{[5,1,none(),domain,result],acc},names,first}
    case Erased{domain,result} Records{acc,names,first}: Records{Con{[5,2,none(),domain,result],acc},names,first}
    case Opaque{name} Records{acc,names,first}: opaque(intern(names,name),acc,first)

def shape_rows(shapes: List<&2,Shape>, rows: Records) -> Records:
  match shapes rows:
    case Nil{} Records{acc,names,next}: Records{List.reverse(&2,List<&2,U32>,acc),names,next}
    case Con{head,tail} Records{acc,names,next}: shape_rows(tail,shape_row(head,Records{acc,names,next}))

def constructor_named(named: Interned, +fields: List<&2,U32>, +type_index: U32, +tag: U32, acc: List<&2,List<&2,U32>>) -> Records:
  match named:
    case Interned{+index,names}: Records{Con{Con{U32.add(5,count(fields)),Con{type_index,Con{tag,Con{index,Con{count(fields),fields}}}}},acc},names,0}

def constructor_row(constructors: List<&2,Constructor>, +type_index: U32, +tag: U32, rows: Records) -> Records:
  match constructors rows:
    case Nil{} Records{acc,names,next}: Records{acc,names,next}
    case Con{Constructor{name,fields},tail} Records{acc,names,next}:
      constructor_row(tail,type_index,U32.add(tag,1),constructor_named(intern(names,name),fields,type_index,tag,acc))

def constructor_rows(shapes: List<&2,Shape>, +type_index: U32, rows: Records) -> Records:
  match shapes rows:
    case Nil{} Records{acc,names,next}: Records{List.reverse(&2,List<&2,U32>,acc),names,next}
    case Con{Algebraic{name,constructors},tail} Records{acc,names,next}:
      constructor_rows(tail,U32.add(type_index,1),constructor_row(constructors,type_index,0,Records{acc,names,next}))
    case Con{other,tail} Records{acc,names,next}: constructor_rows(tail,U32.add(type_index,1),Records{acc,names,next})

type Indexed is Data:
  Indexed{indices: List<&2,U32>, names: Names}

def indexed_name(named: Interned, acc: List<&2,U32>) -> Indexed:
  match named:
    case Interned{index,names}: Indexed{Con{index,acc},names}

def function_names(functions: List<&2,Function>, state: Indexed) -> Indexed:
  match functions state:
    case Nil{} Indexed{acc,names}: Indexed{List.reverse(&2,U32,acc),names}
    case Con{Function{name,parameters,result,slots,body},tail} Indexed{acc,names}:
      function_names(tail,indexed_name(intern(names,name),acc))

type Tables is Data:
  Tables{types: Records, constructors: Records, functions: Indexed}

def tables_finished(constructors: Records, types: Records, functions: List<&2,Function>) -> Tables:
  match constructors:
    case Records{acc,+names,next}: Tables{types,Records{acc,names,next},function_names(functions,Indexed{Nil{},names})}

def tables_named(types: Records, shapes: List<&2,Shape>, functions: List<&2,Function>) -> Tables:
  match types:
    case Records{acc,+names,next}: tables_finished(constructor_rows(shapes,0,Records{Nil{},names,0}),Records{acc,names,next},functions)

# Names, then constructor names, then function names, interned in that order (SPEC section 2).
def tables(+shapes: List<&2,Shape>, functions: List<&2,Function>) -> Tables:
  tables_named(shape_rows(shapes,Records{Nil{},Names{Nil{},0},0}),shapes,functions)

# ---------------------------------------------------------------- node records

# Records are numbered by their absolute word offset. `pool` and `records` hold the newest first.
type Nodes is Data:
  Nodes{records: List<&2,List<&2,U32>>, next: U32, pool: List<&2,Constant>, pooled: U32, sites: U32, nodes: U32}
type Placed is Data:
  Placed{offsets: List<&2,U32>, state: Nodes}

def same_words(xs: List<&2,U32>, ys: List<&2,U32>) -> Bool:
  match xs ys:
    case Nil{} Nil{}: True{}
    case Con{+a,at} Con{+b,bt}: Bool.and(U32.is_eq(a,b),same_words(at,bt))
    case _ _: False{}

def same_constant(a: Constant, b: Constant) -> Bool:
  match a b:
    case Constant{+k,d} Constant{+l,e}: Bool.and(U32.is_eq(k,l),same_words(d,e))

def constant_at(pool: List<&2,Constant>, +constant: Constant, +top: U32) -> Maybe<&2,U32>:
  match pool:
    case Nil{}: None{}
    case Con{+head,+tail}:
      S.choose(Maybe<&2,U32>,same_constant(head,constant),u => Some{top},u => constant_at(tail,constant,U32.sub(top,1)))

def pooled_at(found: Maybe<&2,U32>, state: Nodes, +constant: Constant) -> Placed:
  match found state:
    case Some{index} Nodes{records,next,pool,pooled,sites,nodes}: Placed{Con{index,Nil{}},Nodes{records,next,pool,pooled,sites,nodes}}
    case None{} Nodes{records,next,pool,+pooled,sites,nodes}:
      Placed{Con{pooled,Nil{}},Nodes{records,next,Con{constant,pool},U32.add(pooled,1),sites,nodes}}

def constant_index(state: Nodes, +constant: Constant) -> Placed:
  match state:
    case Nodes{+records,+next,+pool,+pooled,+sites,+nodes}:
      pooled_at(constant_at(pool,constant,U32.sub(pooled,1)),Nodes{records,next,pool,pooled,sites,nodes},constant)

# A record is [length, opcode, result type, operands...]; its offset is the words before it.
def pushed(state: Nodes, +op: U32, +type_id: U32, +operands: List<&2,U32>) -> Result<S.Error,Placed>:
  match state:
    case Nodes{records,+next,pool,pooled,sites,+nodes}:
      S.choose(Result<S.Error,Placed>,U32.is_gt(next,image_words()),u => exhausted(Placed),u =>
        Done{Placed{Con{next,Nil{}},Nodes{Con{Con{U32.add(3,count(operands)),Con{op,Con{type_id,operands}}},records},U32.add(next,U32.add(3,count(operands))),pool,pooled,sites,U32.add(nodes,1)}}})

# [x, n, children...]: Intrinsic, Construct, Application and Foreign.
def counted(placed: Placed, +op: U32, +type_id: U32, +x: U32) -> Result<S.Error,Placed>:
  match placed:
    case Placed{+offsets,state}: pushed(state,op,type_id,Con{x,Con{count(offsets),offsets}})

def literal_node(indexed: Placed, +type_id: U32) -> Result<S.Error,Placed>:
  match indexed:
    case Placed{Con{index,Nil{}},state}: pushed(state,0,type_id,Con{index,Nil{}})
    case _: diagnostic(Placed,"image-literal")

def let_node(value: Placed, body: Placed, +type_id: U32, +slot: U32) -> Result<S.Error,Placed>:
  match value body:
    case Placed{Con{initial,Nil{}},before} Placed{Con{result,Nil{}},state}: pushed(state,7,type_id,[slot,initial,result])
    case _ _: diagnostic(Placed,"image-let")

def invoke_node(function: Placed, arguments: Placed, +type_id: U32) -> Result<S.Error,Placed>:
  match function arguments:
    case Placed{Con{callee,Nil{}},before} Placed{+offsets,state}: pushed(state,11,type_id,Con{callee,Con{count(offsets),offsets}})
    case _ _: diagnostic(Placed,"image-invoke")

def closure_node(body: Placed, +type_id: U32, +live: U32, +slots: U32, +captures: List<&2,U32>) -> Result<S.Error,Placed>:
  match body:
    case Placed{Con{child,Nil{}},Nodes{records,next,pool,pooled,+sites,nodes}}:
      pushed(Nodes{records,next,pool,pooled,U32.add(sites,1),nodes},10,type_id,Con{sites,Con{live,Con{slots,Con{count(captures),List.append(&2,U32,captures,Con{child,Nil{}})}}}})
    case _: diagnostic(Placed,"image-closure")

def default_node(body: Placed, +type_id: U32) -> Result<S.Error,Placed>:
  match body:
    case Placed{Con{child,Nil{}},state}: pushed(state,2,type_id,Con{child,Nil{}})
    case _: diagnostic(Placed,"image-default")

def joined_offsets(first: Placed, rest: Placed) -> Result<S.Error,Placed>:
  match first rest:
    case Placed{offsets,before} Placed{remaining,state}: Done{Placed{List.append(&2,U32,offsets,remaining),state}}

# A tag-mode row is one word: its Branch or `none`; a key-mode row is [key, Branch].
def row_words(placed: Placed, +key: U32, +mode: U32) -> Result<S.Error,Placed>:
  match placed:
    case Placed{Con{+at,Nil{}},state}:
      Done{Placed{S.choose(List<&2,U32>,U32.is_eq(mode,0),u => Con{at,Nil{}},u => Con{key,Con{at,Nil{}}}),state}}
    case _: diagnostic(Placed,"image-row")

def branch_node(body: Placed, +key: U32, +first: U32, +fields: U32, +type_id: U32) -> Result<S.Error,Placed>:
  match body:
    case Placed{Con{child,Nil{}},state}: pushed(state,9,type_id,[key,first,fields,child])
    case _: diagnostic(Placed,"image-branch")

def case_node_record(table: Placed, fallback: Placed, +type_id: U32, +slot: U32, +scrutinee: U32, +mode: U32, +rows: U32) -> Result<S.Error,Placed>:
  match table fallback:
    case Placed{words,before} Placed{Con{last,Nil{}},state}:
      pushed(state,8,type_id,Con{slot,Con{scrutinee,Con{mode,Con{rows,List.append(&2,U32,words,Con{last,Nil{}})}}}})
    case _ _: diagnostic(Placed,"image-case")

def count_rows_onto(rows: List<&2,Row>, +size: U32) -> U32:
  match rows:
    case Nil{}: size
    case Con{head,tail}: count_rows_onto(tail,U32.add(size,1))

def count_rows(rows: List<&2,Row>) -> U32:
  count_rows_onto(rows,0)

type Place is Data:
  One{node: Node}
  Many{nodes: List<&2,Node>}
  More{first: Placed, rest: List<&2,Node>}
  Rowset{rows: List<&2,Row>, mode: U32, type_id: U32}
  Rowed{row: Row, mode: U32, type_id: U32}
  Following{first: Placed, rest: List<&2,Row>, mode: U32, type_id: U32}
  Branched{body: Placed, key: U32, first: U32, fields: U32, mode: U32, type_id: U32}
  Fallback{default: Maybe<&2,Node>, type_id: U32}
  Finish{table: Placed, default: Maybe<&2,Node>, type_id: U32, slot: U32, scrutinee: U32, mode: U32, rows: U32}
  Bodied{value: Placed, body: Node, type_id: U32, slot: U32}
  Applied{function: Placed, arguments: List<&2,Node>, type_id: U32}

# Children are placed before their parent, left to right. The state that a placed child returns is
# the state its next sibling and its parent continue from, so a step that reads it takes the earlier
# result as a mode, never as a matched call.
def place(fuel: Nat, mode: Place, +state: Nodes) -> Result<S.Error,Placed>:
  match fuel mode:
    case 0n _: exhausted(Placed)
    case 1n+ +n One{Literal{+type_id,+constant}}: literal_node(constant_index(state,constant),type_id)
    case 1n+ +n One{Intrinsic{+type_id,+prim,+operands}}:
      S.bind(Placed,Placed,place(n,Many{operands},state),placed => counted(placed,1,type_id,prim))
    case 1n+ +n One{Value{+type_id,+tag}}: pushed(state,3,type_id,Con{tag,Nil{}})
    case 1n+ +n One{Construct{+type_id,+tag,+operands}}:
      S.bind(Placed,Placed,place(n,Many{operands},state),placed => counted(placed,4,type_id,tag))
    case 1n+ +n One{Reference{+type_id,+slot}}: pushed(state,5,type_id,Con{slot,Nil{}})
    case 1n+ +n One{Application{+type_id,+function,+operands}}:
      S.bind(Placed,Placed,place(n,Many{operands},state),placed => counted(placed,6,type_id,function))
    case 1n+ +n One{Let{+type_id,+slot,+value,+body}}:
      S.bind(Placed,Placed,place(n,One{value},state),initial => place(n,Bodied{initial,body,type_id,slot},state))
    case 1n+ +n One{Case{+type_id,+slot,+scrutinee,+mode,+rows,+default}}:
      S.bind(Placed,Placed,place(n,Rowset{rows,mode,type_id},state),table =>
        place(n,Finish{table,default,type_id,slot,scrutinee,mode,count_rows(rows)},state))
    case 1n+ +n One{Closure{+type_id,+live,+slots,+captures,+body}}:
      S.bind(Placed,Placed,place(n,One{body},state),placed => closure_node(placed,type_id,live,slots,captures))
    case 1n+ +n One{Invoke{+type_id,+function,+arguments}}:
      S.bind(Placed,Placed,place(n,One{function},state),callee =>
        place(n,Applied{callee,arguments,type_id},state))
    case 1n+ +n One{Foreign{+type_id,+foreign,+operands}}:
      S.bind(Placed,Placed,place(n,Many{operands},state),placed => counted(placed,12,type_id,foreign))
    case 1n+ +n Many{Nil{}}: Done{Placed{Nil{},state}}
    case 1n+ +n Many{Con{+head,+tail}}:
      S.bind(Placed,Placed,place(n,One{head},state),first => place(n,More{first,tail},state))
    case 1n+ +n More{Placed{offsets,+later},+tail}:
      S.bind(Placed,Placed,place(n,Many{tail},later),rest => joined_offsets(Placed{offsets,later},rest))
    case 1n+ +n Rowset{Nil{},mode,type_id}: Done{Placed{Nil{},state}}
    case 1n+ +n Rowset{Con{+head,+tail},+mode,+type_id}:
      S.bind(Placed,Placed,place(n,Rowed{head,mode,type_id},state),first => place(n,Following{first,tail,mode,type_id},state))
    case 1n+ +n Following{Placed{words,+later},+rest,+mode,+type_id}:
      S.bind(Placed,Placed,place(n,Rowset{rest,mode,type_id},later),remaining => joined_offsets(Placed{words,later},remaining))
    case 1n+ +n Rowed{Missing{},mode,type_id}:
      S.choose(Result<S.Error,Placed>,U32.is_eq(mode,0),u => Done{Placed{Con{none(),Nil{}},state}},u => diagnostic(Placed,"image-missing-key"))
    case 1n+ +n Rowed{Branch{+key,+first,+fields,+body},+mode,+type_id}:
      S.bind(Placed,Placed,place(n,One{body},state),placed => place(n,Branched{placed,key,first,fields,mode,type_id},state))
    case 1n+ +n Branched{Placed{offsets,+later},+key,+first,+fields,+mode,+type_id}:
      S.bind(Placed,Placed,branch_node(Placed{offsets,later},key,first,fields,type_id),branch => row_words(branch,key,mode))
    case 1n+ +n Fallback{None{},type_id}: Done{Placed{Con{none(),Nil{}},state}}
    case 1n+ +n Fallback{Some{+node},+type_id}:
      S.bind(Placed,Placed,place(n,One{node},state),placed => default_node(placed,type_id))
    case 1n+ +n Finish{Placed{words,+later},+default,+type_id,+slot,+scrutinee,+mode,+rows}:
      S.bind(Placed,Placed,place(n,Fallback{default,type_id},later),fallback =>
        case_node_record(Placed{words,later},fallback,type_id,slot,scrutinee,mode,rows))
    case 1n+ +n Bodied{Placed{offsets,+later},+body,+type_id,+slot}:
      S.bind(Placed,Placed,place(n,One{body},later),result => let_node(Placed{offsets,later},result,type_id,slot))
    case 1n+ +n Applied{Placed{offsets,+later},+arguments,+type_id}:
      S.bind(Placed,Placed,place(n,Many{arguments},later),passed => invoke_node(Placed{offsets,later},passed,type_id))

# ---------------------------------------------------------------- names and constants

# Canonical UTF-8. A surrogate takes three bytes and a code from 2^21 keeps a wrapped lead byte,
# as the seed's native lane writes a Char; names hold identifiers, which are ASCII.
def utf8_tail(+code: U32, shift: Nat) -> U32:
  U32.or(128,U32.and(U32.shrn(code,shift),63))

def utf8_code(+code: U32, +rest: List<&2,U32>) -> List<&2,U32>:
  S.choose(List<&2,U32>,U32.is_lt(code,128),u => Con{code,rest},u =>
    S.choose(List<&2,U32>,U32.is_lt(code,2048),u =>
      Con{U32.or(192,U32.shrn(code,6n)),Con{utf8_tail(code,0n),rest}},u =>
      S.choose(List<&2,U32>,U32.is_lt(code,65536),u =>
        Con{U32.or(224,U32.shrn(code,12n)),Con{utf8_tail(code,6n),Con{utf8_tail(code,0n),rest}}},u =>
        Con{U32.and(U32.or(240,U32.shrn(code,18n)),255),Con{utf8_tail(code,12n),Con{utf8_tail(code,6n),Con{utf8_tail(code,0n),rest}}}})))

def utf8(text: String) -> List<&2,U32>:
  match text:
    case SNil{}: Nil{}
    case SCon{head,tail}: utf8_code(Char.to_u32(head),utf8(tail))

# Four bytes to a word, little-endian, the last word padded with zero bytes.
def pack(bytes: List<&2,U32>) -> List<&2,U32>:
  match bytes:
    case Nil{}: Nil{}
    case Con{+a,Nil{}}: Con{a,Nil{}}
    case Con{+a,Con{+b,Nil{}}}: Con{U32.or(a,U32.shln(b,8n)),Nil{}}
    case Con{+a,Con{+b,Con{+c,Nil{}}}}: Con{U32.or(a,U32.or(U32.shln(b,8n),U32.shln(c,16n))),Nil{}}
    case Con{+a,Con{+b,Con{+c,Con{+d,rest}}}}: Con{U32.or(a,U32.or(U32.shln(b,8n),U32.or(U32.shln(c,16n),U32.shln(d,24n)))),pack(rest)}

# [length, byte length, packed bytes...]; names come oldest first.
def name_words(+bytes: List<&2,U32>) -> List<&2,U32>:
  Con{U32.add(2,count(pack(bytes))),Con{count(bytes),pack(bytes)}}

def name_record(text: String) -> List<&2,U32>:
  name_words(utf8(text))

def name_records(names: List<&2,String>, acc: List<&2,List<&2,U32>>) -> List<&2,List<&2,U32>>:
  match names:
    case Nil{}: acc
    case Con{head,tail}: name_records(tail,Con{name_record(head),acc})

def constant_record(constant: Constant) -> List<&2,U32>:
  match constant:
    case Constant{+kind,+data}: Con{U32.add(3,count(data)),Con{kind,Con{count(data),data}}}

def constant_records(pool: List<&2,Constant>, acc: List<&2,List<&2,U32>>) -> List<&2,List<&2,U32>>:
  match pool:
    case Nil{}: acc
    case Con{head,tail}: constant_records(tail,Con{constant_record(head),acc})

# ---------------------------------------------------------------- sections and header

def bodies(functions: List<&2,Function>) -> List<&2,Node>:
  match functions:
    case Nil{}: Nil{}
    case Con{Function{name,parameters,result,slots,body},tail}: Con{body,bodies(tail)}

def main_index(functions: List<&2,Function>, +index: U32) -> U32:
  match functions:
    case Nil{}: none()
    case Con{Function{+name,parameters,result,slots,body},+tail}:
      S.choose(U32,String.eq(name,"main"),u => index,u => main_index(tail,U32.add(index,1)))

def function_limits(parameters: List<&2,U32>, slots: U32) -> Bool:
  Bool.and(U32.is_le(count(parameters),4096),U32.is_le(slots,65536))

# [length, name, result, arity, slots, root, parameters...]
def function_record(function: Function, +index: U32, +root: U32) -> Result<S.Error,List<&2,U32>>:
  match function:
    case Function{name,+parameters,+result,+slots,body}:
      S.choose(Result<S.Error,List<&2,U32>>,function_limits(parameters,slots),u =>
        Done{Con{U32.add(6,count(parameters)),Con{index,Con{result,Con{count(parameters),Con{slots,Con{root,parameters}}}}}}},u => exhausted(List<&2,U32>))

def function_records(functions: List<&2,Function>, indices: List<&2,U32>, roots: List<&2,U32>, acc: List<&2,List<&2,U32>>) -> Result<S.Error,List<&2,List<&2,U32>>>:
  match functions indices roots:
    case Nil{} Nil{} Nil{}: Done{List.reverse(&2,List<&2,U32>,acc)}
    case Con{+head,tail} Con{index,more} Con{root,later}:
      S.bind(List<&2,U32>,List<&2,List<&2,U32>>,function_record(head,index,root),record => function_records(tail,more,later,Con{record,acc}))
    case _ _ _: diagnostic(List<&2,List<&2,U32>>,"image-functions")

# Section sizes in words: a count word, then each record.
def section_words(records: List<&2,List<&2,U32>>) -> U32:
  U32.add(1,total(records))

type Parts is Data:
  Parts{types: List<&2,List<&2,U32>>, constructors: List<&2,List<&2,U32>>, functions: List<&2,List<&2,U32>>, constants: List<&2,List<&2,U32>>,
        nodes: List<&2,List<&2,U32>>, names: List<&2,List<&2,U32>>, node_count: U32, node_words: U32, entry: U32, main: U32, representation: List<&2,U32>}

def header(total_words: U32, entry: U32, main: U32, o1: U32, o2: U32, o3: U32, o4: U32, o5: U32, o6: U32, representation: List<&2,U32>) -> List<&2,U32>:
  List.append(&2,U32,[magic(),1,total_words,entry,main,o1,o2,o3,o4,o5,o6,0],List.append(&2,U32,representation,digest()))

def count_records(rows: List<&2,List<&2,U32>>, +size: U32) -> U32:
  match rows:
    case Nil{}: size
    case Con{head,tail}: count_records(tail,U32.add(size,1))

# A section is its record count, then its records. The nodes arrive newest first and are reversed
# onto the names section, so the largest list is not copied.
def section(+rows: List<&2,List<&2,U32>>, +tail: List<&2,List<&2,U32>>) -> List<&2,List<&2,U32>>:
  Con{[count_records(rows,0)],List.append(&2,List<&2,U32>,rows,tail)}

def image_records(parts: Parts, header_words: List<&2,U32>) -> List<&2,List<&2,U32>>:
  match parts:
    case Parts{types,constructors,functions,constants,nodes,names,+node_count,node_words,entry,main,representation}:
      +named : List<&2,List<&2,U32>> = section(names,Nil{})
      +noded : List<&2,List<&2,U32>> = Con{[node_count],List.reverse.go(&2,List<&2,U32>,nodes,named)}
      +pooled : List<&2,List<&2,U32>> = section(constants,noded)
      +called : List<&2,List<&2,U32>> = section(functions,pooled)
      +typed : List<&2,List<&2,U32>> = section(constructors,called)
      Con{header_words,section(types,typed)}

type Encoded is Data:
  Encoded{records: List<&2,List<&2,U32>>, words: U32}

def within_limits(+types: List<&2,List<&2,U32>>, +constructors: List<&2,List<&2,U32>>, +functions: List<&2,List<&2,U32>>, +constants: List<&2,List<&2,U32>>, +nodes: U32, +names: List<&2,List<&2,U32>>) -> Bool:
  Bool.and(U32.is_le(count_records(types,0),table_records()),Bool.and(U32.is_le(count_records(constructors,0),table_records()),
    Bool.and(U32.is_le(count_records(functions,0),table_records()),Bool.and(U32.is_le(count_records(constants,0),table_records()),
    Bool.and(U32.is_le(nodes,table_records()),U32.is_le(count_records(names,0),table_records()))))))

# The header offsets follow from the section sizes; the size and the record limits of SPEC section 4
# are checked before any word exists, so no layout is produced for an image the VM would refuse.
def layout_sections(+frecords: List<&2,List<&2,U32>>, +off_nodes: U32, +end: U32, +types: List<&2,List<&2,U32>>, +constructors: List<&2,List<&2,U32>>,
    +constants: List<&2,List<&2,U32>>, nodes: List<&2,List<&2,U32>>, +node_count: U32, +named: List<&2,List<&2,U32>>, +entry: U32, +main: U32, +representation: List<&2,U32>) -> Result<S.Error,Encoded>:
  +o2 = U32.add(32,section_words(types))
  +o3 = U32.add(o2,section_words(constructors))
  +o4 = U32.add(o3,section_words(frecords))
  +o6 = U32.add(off_nodes,U32.sub(end,off_nodes))
  +total_words = U32.add(o6,section_words(named))
  S.choose(Result<S.Error,Encoded>,U32.is_eq(off_nodes,U32.add(o4,section_words(constants))),u =>
    S.choose(Result<S.Error,Encoded>,Bool.and(U32.is_le(total_words,image_words()),within_limits(types,constructors,frecords,constants,node_count,named)),u =>
      Done{Encoded{image_records(Parts{types,constructors,frecords,constants,nodes,named,node_count,U32.sub(end,off_nodes),entry,main,representation},
        header(total_words,entry,main,32,o2,o3,o4,off_nodes,o6,representation)),total_words}},u => exhausted(Encoded)),u => diagnostic(Encoded,"image-layout"))

def name_list(names: Names) -> List<&2,String>:
  match names:
    case Names{list,size}: list

def layout_final(final: Placed, +off_nodes: U32, +types: List<&2,List<&2,U32>>, +constructors: List<&2,List<&2,U32>>, +indices: List<&2,U32>, +names: Names,
    +entry: U32, +representation: List<&2,U32>, +functions: List<&2,Function>) -> Result<S.Error,Encoded>:
  match final:
    case Placed{+roots,Nodes{nodes,+end,+pool,pooled,sites,+node_count}}:
      S.bind(List<&2,List<&2,U32>>,Encoded,function_records(functions,indices,roots,Nil{}),frecords =>
        layout_sections(frecords,off_nodes,end,types,constructors,constant_records(pool,Nil{}),nodes,node_count,name_records(name_list(names),Nil{}),entry,main_index(functions,0),representation))

# Pass two places the nodes at their final offsets. The constants pool is interned in the same order
# as in the trial pass, so the constants section, which precedes the nodes, has the size it had.
def layout_nodes(fuel: Nat, +off_nodes: U32, +types: List<&2,List<&2,U32>>, +constructors: List<&2,List<&2,U32>>, +indices: List<&2,U32>, +names: Names,
    +entry: U32, +representation: List<&2,U32>, +functions: List<&2,Function>) -> Result<S.Error,Encoded>:
  S.bind(Placed,Encoded,place(fuel,Many{bodies(functions)},Nodes{Nil{},U32.add(off_nodes,1),Nil{},0,0,0}),final =>
    layout_final(final,off_nodes,types,constructors,indices,names,entry,representation,functions))

def layout_trial(fuel: Nat, trial: Placed, +types: List<&2,List<&2,U32>>, +constructors: List<&2,List<&2,U32>>, +indices: List<&2,U32>, +names: Names,
    +entry: U32, +representation: List<&2,U32>, +functions: List<&2,Function>) -> Result<S.Error,Encoded>:
  match trial:
    case Placed{+roots,Nodes{nodes,end,+pool,pooled,sites,node_count}}:
      S.bind(List<&2,List<&2,U32>>,Encoded,function_records(functions,indices,roots,Nil{}),sized =>
        layout_nodes(fuel,U32.add(32,U32.add(section_words(types),U32.add(section_words(constructors),U32.add(section_words(sized),section_words(constant_records(pool,Nil{})))))),
          types,constructors,indices,names,entry,representation,functions))

def layout_tables(+fuel: Nat, grid: Tables, +entry: U32, +representation: List<&2,U32>, +functions: List<&2,Function>) -> Result<S.Error,Encoded>:
  match grid:
    case Tables{Records{+types,tnames,tnext},Records{+constructors,cnames,cnext},Indexed{+indices,+names}}:
      S.bind(Placed,Encoded,place(fuel,Many{bodies(functions)},Nodes{Nil{},0,Nil{},0,0,0}),trial =>
        layout_trial(fuel,trial,types,constructors,indices,names,entry,representation,functions))

# The words of an image: header, then the six sections, as records that the writer streams in order.
def layout(fuel: Nat, plan: Plan) -> Result<S.Error,Encoded>:
  match plan:
    case Plan{entry,representation,+shapes,+functions}:
      layout_tables(fuel,tables(shapes,functions),entry,representation,functions)

def encode(+fuel: Nat, book: C.Book) -> Result<S.Error,Encoded>:
  S.bind(Plan,Encoded,erase_tokens(fuel,book),plan => layout(fuel,plan))

# ---------------------------------------------------------------- byte stream

# The image is written in chunks of at most 16,384 steps (a word or a record boundary), that is at
# most 65,536 bytes, so the writer never holds the image as one byte list.
type Cursor is Data:
  Cursor{words: List<&2,U32>, records: List<&2,List<&2,U32>>}
type Filled is Data:
  Filled{bytes: List<&2,U32>, rest: Cursor}
type Step is Data:
  Chunk{bytes: List<&2,U32>, rest: Cursor}
  End{}

def chunk_steps() -> Nat:
  16384n

def start(encoded: Encoded) -> Cursor:
  match encoded:
    case Encoded{records,words}: Cursor{Nil{},records}

# The newest byte is first: the reversal at the end of a chunk puts a word's low byte first.
def word_bytes(+word: U32, acc: List<&2,U32>) -> List<&2,U32>:
  Con{U32.shrn(word,24n),Con{U32.and(U32.shrn(word,16n),255),Con{U32.and(U32.shrn(word,8n),255),Con{U32.and(word,255),acc}}}}

def take(budget: Nat, cursor: Cursor, acc: List<&2,U32>) -> Filled:
  match budget cursor:
    case 0n cursor: Filled{acc,cursor}
    case 1n+ +n Cursor{Con{word,rest},records}: take(n,Cursor{rest,records},word_bytes(word,acc))
    case 1n+ +n Cursor{Nil{},Con{record,later}}: take(n,Cursor{record,later},acc)
    case 1n+ +n Cursor{Nil{},Nil{}}: Filled{acc,Cursor{Nil{},Nil{}}}

def stepped(filled: Filled) -> Step:
  match filled:
    case Filled{Nil{},rest}: End{}
    case Filled{+bytes,rest}: Chunk{List.reverse(&2,U32,bytes),rest}

def pull(cursor: Cursor) -> Step:
  stepped(take(chunk_steps(),cursor,Nil{}))

# ---------------------------------------------------------------- decoding

# A refused image is `HostFailure image` with the reason of vm/serializer.py where it has one; an
# image past a resource limit of SPEC section 4 is exhausted, never malformed.
def malformed(-A: Type, reason: String) -> Result<S.Error,A>:
  Fail{S.Host{"image",reason}}

# A record of a section: its payload (the words after its length word) and its offset.
type Located is Data:
  Located{at: U32, words: List<&2,U32>}
type Read is Data:
  Read{items: List<&2,Located>, rest: List<&2,U32>, at: U32}

# One word per step: `Counting` expects a section's count, `Length` the length word of the next
# record and `Payload` the words left in the current one.
type Reader is Data:
  Counting{at: U32}
  Length{count: U32, at: U32, items: List<&2,Located>}
  Payload{count: U32, left: U32, start: U32, at: U32, payload: List<&2,U32>, items: List<&2,Located>}

def finished(items: List<&2,Located>, rest: List<&2,U32>, at: U32) -> Result<S.Error,Read>:
  Done{Read{List.reverse(&2,Located,items),rest,at}}

# The record limit is checked when the count is read (SPEC section 4), before anything it governs.
def read_section(words: List<&2,U32>, reader: Reader) -> Result<S.Error,Read>:
  match words reader:
    case Nil{} _: malformed(Read,"truncated")
    case Con{+count,+tail} Counting{+at}:
      S.choose(Result<S.Error,Read>,U32.is_gt(count,table_records()),u => exhausted(Read),u =>
        S.choose(Result<S.Error,Read>,U32.is_eq(count,0),u => finished(Nil{},tail,U32.add(at,1)),u => read_section(tail,Length{count,U32.add(at,1),Nil{}})))
    case Con{+length,tail} Length{+count,+at,items}:
      S.choose(Result<S.Error,Read>,U32.is_lt(length,2),u => malformed(Read,"record length"),u =>
        read_section(tail,Payload{count,U32.sub(length,1),at,U32.add(at,1),Nil{},items}))
    case Con{+word,+tail} Payload{+count,+left,+start,+at,+payload,+items}:
      S.choose(Result<S.Error,Read>,U32.is_gt(left,1),u => read_section(tail,Payload{count,U32.sub(left,1),start,U32.add(at,1),Con{word,payload},items}),u =>
        S.choose(Result<S.Error,Read>,U32.is_eq(count,1),u => finished(Con{Located{start,List.reverse(&2,U32,Con{word,payload})},items},tail,U32.add(at,1)),u =>
          read_section(tail,Length{U32.sub(count,1),U32.add(at,1),Con{Located{start,List.reverse(&2,U32,Con{word,payload})},items}})))

def section_read(words: List<&2,U32>, +at: U32) -> Result<S.Error,Read>:
  read_section(words,Counting{at})

type Split is Data:
  Split{head: List<&2,U32>, rest: List<&2,U32>}

def split_words(count: Nat, words: List<&2,U32>, acc: List<&2,U32>) -> Result<S.Error,Split>:
  match count words:
    case 0n words: Done{Split{List.reverse(&2,U32,acc),words}}
    case 1n+ +n Con{head,tail}: split_words(n,tail,Con{head,acc})
    case 1n+ +n Nil{}: malformed(Split,"length")

type Header is Data:
  Header{total: U32, entry: U32, main: U32, offsets: List<&2,U32>, representation: List<&2,U32>}

def parsed_header(head: List<&2,U32>) -> Result<S.Error,Header>:
  match head:
    case Con{+magic_word,Con{+version,Con{+total,Con{+entry,Con{+main,Con{+o1,Con{+o2,Con{+o3,Con{+o4,Con{+o5,Con{+o6,Con{+reserved,Con{+r0,Con{+r1,Con{+r2,Con{+r3,Con{+r4,Con{+r5,Con{+r6,Con{+r7,Con{+r8,Con{+r9,Con{+r10,Con{+r11,Con{+d0,Con{+d1,Con{+d2,Con{+d3,Con{+d4,Con{+d5,Con{+d6,Con{+d7,Nil{}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}:
      S.choose(Result<S.Error,Header>,Bool.and(U32.is_eq(magic_word,magic()),U32.is_eq(version,1)),u =>
        S.choose(Result<S.Error,Header>,Bool.and(U32.is_lt(entry,2),U32.is_eq(reserved,0)),u =>
          S.choose(Result<S.Error,Header>,same_words([d0,d1,d2,d3,d4,d5,d6,d7],digest()),u =>
            Done{Header{total,entry,main,[o1,o2,o3,o4,o5,o6],[r0,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11]}},u => malformed(Header,"registry digest")),u => malformed(Header,"header")),u => malformed(Header,"magic"))
    case _: malformed(Header,"length")

type Gathered is Data:
  Gathered{sections: List<&2,List<&2,Located>>, rest: List<&2,U32>, at: U32}
type Stage is Data:
  Fresh{words: List<&2,U32>, at: U32, done: List<&2,List<&2,Located>>}
  Fetched{read: Read, later: List<&2,U32>, done: List<&2,List<&2,Located>>}

# The six sections follow the header in order, adjacent, from the offsets the header names.
def read_sections(fuel: Nat, offsets: List<&2,U32>, stage: Stage) -> Result<S.Error,Gathered>:
  match fuel offsets stage:
    case 0n _ _: malformed(Gathered,"sections")
    case 1n+ +n Nil{} Fresh{words,at,done}: Done{Gathered{List.reverse(&2,List<&2,Located>,done),words,at}}
    case 1n+ +n Con{+offset,+later} Fresh{+words,+at,done}:
      S.choose(Result<S.Error,Gathered>,U32.is_eq(at,offset),u =>
        S.bind(Read,Gathered,section_read(words,at),read => read_sections(n,Nil{},Fetched{read,later,done})),u => malformed(Gathered,"section offset"))
    case 1n+ +n offsets Fetched{Read{items,rest,at},later,done}: read_sections(n,later,Fresh{rest,at,Con{items,done}})

# Names hold identifiers: bytes 1..127. A wider name is refused as unsupported, never misread.
def ascii_text(bytes: List<&2,U32>, acc: String) -> Result<S.Error,String>:
  match bytes:
    case Nil{}: Done{String.reverse(acc)}
    case Con{+byte,+tail}:
      S.choose(Result<S.Error,String>,U32.is_eq(byte,0),u => malformed(String,"name padding"),u =>
        S.choose(Result<S.Error,String>,U32.is_lt(byte,128),u => ascii_text(tail,SCon{Char.from_u32(byte),acc}),u => unsupported(String,"image-name")))

def unpacked(words: List<&2,U32>) -> List<&2,U32>:
  match words:
    case Nil{}: Nil{}
    case Con{+word,tail}:
      Con{U32.and(word,255),Con{U32.and(U32.shrn(word,8n),255),Con{U32.and(U32.shrn(word,16n),255),Con{U32.shrn(word,24n),unpacked(tail)}}}}

def zeros(bytes: List<&2,U32>) -> Bool:
  match bytes:
    case Nil{}: True{}
    case Con{byte,tail}: Bool.and(U32.is_eq(byte,0),zeros(tail))

def named(split: Split) -> Result<S.Error,String>:
  match split:
    case Split{used,rest}:
      S.choose(Result<S.Error,String>,zeros(rest),u => ascii_text(used,SNil{}),u => malformed(String,"name padding"))

def name_text(located: Located) -> Result<S.Error,String>:
  match located:
    case Located{at,Con{+size,+packed}}:
      S.choose(Result<S.Error,String>,Bool.and(U32.is_gt(size,0),U32.is_eq(count(packed),U32.shrn(U32.add(size,3),2n))),u =>
        S.bind(Split,String,split_words(U32.to_nat(size),unpacked(packed),Nil{}),split => named(split)),u => malformed(String,"name length"))
    case _: malformed(String,"name length")

def has_name(seen: List<&2,String>, +text: String) -> Bool:
  match seen:
    case Nil{}: False{}
    case Con{head,tail}: Bool.or(String.eq(head,text),has_name(tail,text))

# Names come oldest first; `seen` holds them newest first while they are read.
def decoded_names(records: List<&2,Located>, +seen: List<&2,String>) -> Result<S.Error,List<&2,String>>:
  match records:
    case Nil{}: Done{List.reverse(&2,String,seen)}
    case Con{head,tail}:
      S.bind(String,List<&2,String>,name_text(head),+text =>
        S.choose(Result<S.Error,List<&2,String>>,has_name(seen,text),u => malformed(List<&2,String>,"duplicate name"),u => decoded_names(tail,Con{text,seen})))

def name_at(names: List<&2,String>, +index: U32) -> Result<S.Error,String>:
  match names:
    case Nil{}: malformed(String,"name index")
    case Con{+head,+tail}: S.choose(Result<S.Error,String>,U32.is_eq(index,0),u => Done{head},u => name_at(tail,U32.sub(index,1)))

# [kind, n, data...]: a scalar holds one word, a String its Chr codes.
def decode_constant(located: Located) -> Result<S.Error,Constant>:
  match located:
    case Located{at,Con{+kind,Con{+n,+data}}}:
      S.choose(Result<S.Error,Constant>,Bool.and(U32.is_lt(kind,4),U32.is_eq(count(data),n)),u =>
        S.choose(Result<S.Error,Constant>,Bool.or(U32.is_eq(kind,3),U32.is_eq(n,1)),u => Done{Constant{kind,data}},u => malformed(Constant,"scalar constant width")),u => malformed(Constant,"constant record"))
    case _: malformed(Constant,"constant record")

def decoded_constants(records: List<&2,Located>) -> Result<S.Error,List<&2,Constant>>:
  match records:
    case Nil{}: Done{Nil{}}
    case Con{head,tail}:
      S.bind(Constant,List<&2,Constant>,decode_constant(head),constant =>
        S.bind(List<&2,Constant>,List<&2,Constant>,decoded_constants(tail),rest => Done{Con{constant,rest}}))

def constant_of(constants: List<&2,Constant>, +index: U32) -> Result<S.Error,Constant>:
  match constants:
    case Nil{}: malformed(Constant,"constant index")
    case Con{+head,+tail}: S.choose(Result<S.Error,Constant>,U32.is_eq(index,0),u => Done{head},u => constant_of(tail,U32.sub(index,1)))

type Grouped is Data:
  Grouped{constructors: List<&2,Constructor>, rest: List<&2,Located>}

def decode_constructors(left: Nat, records: List<&2,Located>, +type_index: U32, +tag: U32, +names: List<&2,String>, acc: List<&2,Constructor>) -> Result<S.Error,Grouped>:
  match left records:
    case 0n records: Done{Grouped{List.reverse(&2,Constructor,acc),records}}
    case 1n+ +n Con{Located{at,Con{+owner,Con{+index,Con{+name,Con{+arity,+fields}}}}},+rest}:
      S.choose(Result<S.Error,Grouped>,Bool.and(U32.is_eq(owner,type_index),Bool.and(U32.is_eq(index,tag),U32.is_eq(count(fields),arity))),u =>
        S.bind(String,Grouped,name_at(names,name),text => decode_constructors(n,rest,type_index,U32.add(tag,1),names,Con{Constructor{text,fields},acc})),u => malformed(Grouped,"constructor record"))
    case 1n+ +n Con{other,rest}: malformed(Grouped,"constructor record")
    case 1n+ +n Nil{}: malformed(Grouped,"constructor count")

type Shaped is Data:
  Shaped{shapes: List<&2,Shape>, constructors: List<&2,Located>}

type Shaping is Data:
  Next{types: List<&2,Located>, constructors: List<&2,Located>, first: U32, index: U32, acc: List<&2,Shape>}
  Taken{grouped: Grouped, text: String, types: List<&2,Located>, first: U32, index: U32, acc: List<&2,Shape>}

def arrow_kind(+kind: U32, +domain: U32, +result: U32) -> Shape:
  Bool.pick(Shape,U32.is_eq(kind,1),Arrow{domain,result},Erased{domain,result})

# Types are read in table order; a constructor row belongs to the type that owns it, densely tagged.
def decode_shapes(fuel: Nat, +names: List<&2,String>, mode: Shaping) -> Result<S.Error,Shaped>:
  match fuel mode:
    case 0n _: malformed(Shaped,"types")
    case 1n+ +n Next{Nil{},constructors,first,index,acc}: Done{Shaped{List.reverse(&2,Shape,acc),constructors}}
    case 1n+ +n Next{Con{Located{at,Con{+kind,Con{+name,Con{+a,Con{+b,Nil{}}}}}},+tail},+constructors,+first,+index,+acc}:
      S.choose(Result<S.Error,Shaped>,U32.is_eq(kind,0),u =>
        S.choose(Result<S.Error,Shaped>,U32.is_eq(a,first),u =>
          S.bind(String,Shaped,name_at(names,name),+text =>
            S.bind(Grouped,Shaped,decode_constructors(U32.to_nat(b),constructors,index,0,names,Nil{}),grouped =>
              decode_shapes(n,names,Taken{grouped,text,tail,U32.add(first,b),index,acc}))),u => malformed(Shaped,"constructor grouping")),u =>
        S.choose(Result<S.Error,Shaped>,Bool.or(U32.is_eq(kind,1),U32.is_eq(kind,2)),u =>
          S.choose(Result<S.Error,Shaped>,U32.is_eq(name,none()),u =>
            decode_shapes(n,names,Next{tail,constructors,first,U32.add(index,1),Con{arrow_kind(kind,a,b),acc}}),u => malformed(Shaped,"arrow name")),u =>
          S.choose(Result<S.Error,Shaped>,Bool.and(U32.is_eq(kind,3),Bool.and(U32.is_eq(a,0),U32.is_eq(b,0))),u =>
            S.bind(String,Shaped,name_at(names,name),text => decode_shapes(n,names,Next{tail,constructors,first,U32.add(index,1),Con{Opaque{text},acc}})),u => malformed(Shaped,"type record"))))
    case 1n+ +n Next{other,constructors,first,index,acc}: malformed(Shaped,"type record")
    case 1n+ +n Taken{Grouped{constructors,rest},text,tail,first,index,acc}:
      decode_shapes(n,names,Next{tail,rest,first,U32.add(index,1),Con{Algebraic{text,constructors},acc}})

type Head is Data:
  Head{name: String, result: U32, slots: U32, root: U32, parameters: List<&2,U32>}

def decode_head(located: Located, names: List<&2,String>) -> Result<S.Error,Head>:
  match located:
    case Located{at,Con{+name,Con{+result,Con{+arity,Con{+slots,Con{+root,+parameters}}}}}}:
      S.choose(Result<S.Error,Head>,U32.is_eq(count(parameters),arity),u =>
        S.choose(Result<S.Error,Head>,U32.is_gt(arity,4096),u => exhausted(Head),u =>
          S.choose(Result<S.Error,Head>,U32.is_gt(slots,65536),u => exhausted(Head),u =>
            S.bind(String,Head,name_at(names,name),text => Done{Head{text,result,slots,root,parameters}}))),u => malformed(Head,"function record"))
    case _: malformed(Head,"function record")

def decode_heads(records: List<&2,Located>, +names: List<&2,String>) -> Result<S.Error,List<&2,Head>>:
  match records:
    case Nil{}: Done{Nil{}}
    case Con{head,tail}:
      S.bind(Head,List<&2,Head>,decode_head(head,names),first =>
        S.bind(List<&2,Head>,List<&2,Head>,decode_heads(tail,names),rest => Done{Con{first,rest}}))

# ---------------------------------------------------------------- the node stream

# Nodes are read in emission order. A record's children are the newest entries of the stack, in
# order, and the record takes their place: each node has one parent, and the roots that remain are
# the functions' bodies. The offsets a record lists must be the offsets of the entries it takes.
type Item is Data:
  Whole{node: Node}
  Branching{row: Row}
  Defaulted{node: Node}
type Entry is Data:
  Entry{at: U32, item: Item}
type Popped is Data:
  Popped{entries: List<&2,Entry>, rest: List<&2,Entry>}
type Children is Data:
  Children{nodes: List<&2,Node>, rest: List<&2,Entry>}

def pop(remaining: Nat, stack: List<&2,Entry>, acc: List<&2,Entry>) -> Result<S.Error,Popped>:
  match remaining stack:
    case 0n stack: Done{Popped{acc,stack}}
    case 1n+ +n Con{entry,rest}: pop(n,rest,Con{entry,acc})
    case 1n+ +n Nil{}: malformed(Popped,"child offset")

def child_nodes(entries: List<&2,Entry>, offsets: List<&2,U32>) -> Result<S.Error,List<&2,Node>>:
  match entries offsets:
    case Nil{} Nil{}: Done{Nil{}}
    case Con{Entry{+at,Whole{node}},more} Con{+offset,later}:
      S.choose(Result<S.Error,List<&2,Node>>,U32.is_eq(at,offset),u =>
        S.bind(List<&2,Node>,List<&2,Node>,child_nodes(more,later),rest => Done{Con{node,rest}}),u => malformed(List<&2,Node>,"child offset"))
    case _ _: malformed(List<&2,Node>,"child offset")

def collected(popped: Popped, offsets: List<&2,U32>) -> Result<S.Error,Children>:
  match popped:
    case Popped{entries,rest}: S.bind(List<&2,Node>,Children,child_nodes(entries,offsets),nodes => Done{Children{nodes,rest}})

def children(+offsets: List<&2,U32>, stack: List<&2,Entry>) -> Result<S.Error,Children>:
  S.bind(Popped,Children,pop(U32.to_nat(count(offsets)),stack,Nil{}),popped => collected(popped,offsets))

def entry_of(node: Node, +at: U32, rest: List<&2,Entry>) -> Result<S.Error,List<&2,Entry>>:
  Done{Con{Entry{at,Whole{node}},rest}}

def counted_entry(op: U32, kids: Children, +at: U32, +type_id: U32, +x: U32) -> Result<S.Error,List<&2,Entry>>:
  match op kids:
    case 1 Children{nodes,rest}: entry_of(Intrinsic{type_id,x,nodes},at,rest)
    case 4 Children{nodes,rest}: entry_of(Construct{type_id,x,nodes},at,rest)
    case 6 Children{nodes,rest}: entry_of(Application{type_id,x,nodes},at,rest)
    case 12 Children{nodes,rest}: entry_of(Foreign{type_id,x,nodes},at,rest)
    case _ _: malformed(List<&2,Entry>,"opcode")

# [x, n, children...]: Intrinsic, Construct, Application and Foreign.
def counted_operation(op: U32, x: List<&2,U32>, at: U32, type_id: U32, stack: List<&2,Entry>) -> Result<S.Error,List<&2,Entry>>:
  match x:
    case Con{+first,Con{+n,+offsets}}:
      S.choose(Result<S.Error,List<&2,Entry>>,U32.is_eq(count(offsets),n),u =>
        S.bind(Children,List<&2,Entry>,children(offsets,stack),kids => counted_entry(op,kids,at,type_id,first)),u => malformed(List<&2,Entry>,"operand count"))
    case _: malformed(List<&2,Entry>,"operand count")

def literal_operation(x: List<&2,U32>, +at: U32, +type_id: U32, stack: List<&2,Entry>, constants: List<&2,Constant>) -> Result<S.Error,List<&2,Entry>>:
  match x:
    case Con{index,Nil{}}: S.bind(Constant,List<&2,Entry>,constant_of(constants,index),constant => entry_of(Literal{type_id,constant},at,stack))
    case _: malformed(List<&2,Entry>,"lit length")

def scalar_operation(op: U32, x: List<&2,U32>, +at: U32, +type_id: U32, stack: List<&2,Entry>) -> Result<S.Error,List<&2,Entry>>:
  match op x:
    case 3 Con{tag,Nil{}}: entry_of(Value{type_id,tag},at,stack)
    case 5 Con{slot,Nil{}}: entry_of(Reference{type_id,slot},at,stack)
    case _ _: malformed(List<&2,Entry>,"node length")

def let_built(kids: Children, +at: U32, +type_id: U32, +slot: U32) -> Result<S.Error,List<&2,Entry>>:
  match kids:
    case Children{Con{value,Con{body,Nil{}}},rest}: entry_of(Let{type_id,slot,value,body},at,rest)
    case _: malformed(List<&2,Entry>,"let length")

def let_operation(x: List<&2,U32>, +at: U32, +type_id: U32, stack: List<&2,Entry>) -> Result<S.Error,List<&2,Entry>>:
  match x:
    case Con{+slot,Con{value,Con{body,Nil{}}}}:
      S.bind(Children,List<&2,Entry>,children([value,body],stack),kids => let_built(kids,at,type_id,slot))
    case _: malformed(List<&2,Entry>,"let length")

def body_entry(kids: Children, +op: U32, +at: U32, +a: U32, +b: U32, +c: U32) -> Result<S.Error,List<&2,Entry>>:
  match kids:
    case Children{Con{+node,Nil{}},+rest}:
      S.choose(Result<S.Error,List<&2,Entry>>,U32.is_eq(op,9),u => Done{Con{Entry{at,Branching{Branch{a,b,c,node}}},rest}},u => Done{Con{Entry{at,Defaulted{node}},rest}})
    case _: malformed(List<&2,Entry>,"body length")

def branch_operation(x: List<&2,U32>, at: U32, stack: List<&2,Entry>) -> Result<S.Error,List<&2,Entry>>:
  match x:
    case Con{+key,Con{+first,Con{+fields,Con{body,Nil{}}}}}: S.bind(Children,List<&2,Entry>,children([body],stack),kids => body_entry(kids,9,at,key,first,fields))
    case _: malformed(List<&2,Entry>,"branch length")

def default_operation(x: List<&2,U32>, at: U32, stack: List<&2,Entry>) -> Result<S.Error,List<&2,Entry>>:
  match x:
    case Con{body,Nil{}}: S.bind(Children,List<&2,Entry>,children([body],stack),kids => body_entry(kids,2,at,0,0,0))
    case _: malformed(List<&2,Entry>,"default length")

def closure_built(captures: List<&2,U32>, kids: Children, +at: U32, +type_id: U32, +live: U32, +slots: U32) -> Result<S.Error,List<&2,Entry>>:
  match kids:
    case Children{Con{node,Nil{}},rest}: entry_of(Closure{type_id,live,slots,captures,node},at,rest)
    case _: malformed(List<&2,Entry>,"closure length")

def closure_kids(split: Split, stack: List<&2,Entry>, +at: U32, +type_id: U32, +live: U32, +slots: U32) -> Result<S.Error,List<&2,Entry>>:
  match split:
    case Split{+captures,Con{body,Nil{}}}:
      S.bind(Children,List<&2,Entry>,children([body],stack),kids => closure_built(captures,kids,at,type_id,live,slots))
    case _: malformed(List<&2,Entry>,"closure length")

def closure_operation(x: List<&2,U32>, +at: U32, +type_id: U32, stack: List<&2,Entry>) -> Result<S.Error,List<&2,Entry>>:
  match x:
    case Con{site,Con{+live,Con{+slots,Con{+n,+rest}}}}:
      S.bind(Split,List<&2,Entry>,split_words(U32.to_nat(n),rest,Nil{}),+split => closure_kids(split,stack,at,type_id,live,slots))
    case _: malformed(List<&2,Entry>,"closure length")

def invoke_built(kids: Children, +at: U32, +type_id: U32) -> Result<S.Error,List<&2,Entry>>:
  match kids:
    case Children{Con{callee,arguments},rest}: entry_of(Invoke{type_id,callee,arguments},at,rest)
    case _: malformed(List<&2,Entry>,"invoke length")

def invoke_operation(x: List<&2,U32>, +at: U32, +type_id: U32, stack: List<&2,Entry>) -> Result<S.Error,List<&2,Entry>>:
  match x:
    case Con{+function,Con{+n,+arguments}}:
      S.choose(Result<S.Error,List<&2,Entry>>,U32.is_eq(count(arguments),n),u =>
        S.bind(Children,List<&2,Entry>,children(Con{function,arguments},stack),kids => invoke_built(kids,at,type_id)),u => malformed(List<&2,Entry>,"invoke length"))
    case _: malformed(List<&2,Entry>,"invoke length")

type Rowing is Data:
  Rowing{rows: List<&2,Row>, rest: List<&2,Entry>}

def row_prepended(row: Row, rowing: Rowing) -> Result<S.Error,Rowing>:
  match rowing:
    case Rowing{rows,rest}: Done{Rowing{Con{row,rows},rest}}

# The rows of a Case, from its row words and the arms that its record takes: a tag row is an arm's
# offset or `none`, a key row is a key and an arm whose own key it repeats.
def rows_from(mode: U32, words: List<&2,U32>, entries: List<&2,Entry>) -> Result<S.Error,Rowing>:
  match mode words entries:
    case 0 Nil{} entries: Done{Rowing{Nil{},entries}}
    case 0 Con{4294967295,more} entries: S.bind(Rowing,Rowing,rows_from(0,more,entries),rest => row_prepended(Missing{},rest))
    case 0 Con{+w,more} Con{Entry{+at,Branching{row}},later}:
      S.choose(Result<S.Error,Rowing>,U32.is_eq(at,w),u => S.bind(Rowing,Rowing,rows_from(0,more,later),rest => row_prepended(row,rest)),u => malformed(Rowing,"case arm"))
    case 1 Nil{} entries: Done{Rowing{Nil{},entries}}
    case 1 Con{+key,Con{+w,more}} Con{Entry{+at,Branching{Branch{+k,first,fields,body}}},later}:
      S.choose(Result<S.Error,Rowing>,Bool.and(U32.is_eq(at,w),U32.is_eq(k,key)),u =>
        S.bind(Rowing,Rowing,rows_from(1,more,later),rest => row_prepended(Branch{k,first,fields,body},rest)),u => malformed(Rowing,"case key"))
    case _ _ _: malformed(Rowing,"case arm")

def arm_offsets(mode: U32, words: List<&2,U32>) -> List<&2,U32>:
  match mode words:
    case 0 Nil{}: Nil{}
    case 0 Con{4294967295,more}: arm_offsets(0,more)
    case 0 Con{w,more}: Con{w,arm_offsets(0,more)}
    case 1 Con{key,Con{w,more}}: Con{w,arm_offsets(1,more)}
    case _ _: Nil{}

def case_done(rowing: Rowing, +default: U32, below: List<&2,Entry>, +at: U32, +type_id: U32, +slot: U32, +scrutinee: U32, +mode: U32) -> Result<S.Error,List<&2,Entry>>:
  match rowing:
    case Rowing{rows,Nil{}}:
      S.choose(Result<S.Error,List<&2,Entry>>,U32.is_eq(default,none()),u => entry_of(Case{type_id,slot,scrutinee,mode,rows,None{}},at,below),u => malformed(List<&2,Entry>,"case default"))
    case Rowing{rows,Con{Entry{+d,Defaulted{node}},Nil{}}}:
      S.choose(Result<S.Error,List<&2,Entry>>,U32.is_eq(default,d),u => entry_of(Case{type_id,slot,scrutinee,mode,rows,Some{node}},at,below),u => malformed(List<&2,Entry>,"case default"))
    case _: malformed(List<&2,Entry>,"case arm kind")

def case_after(popped: Popped, words: List<&2,U32>, +default: U32, +at: U32, +type_id: U32, +slot: U32, +scrutinee: U32, +mode: U32) -> Result<S.Error,List<&2,Entry>>:
  match popped:
    case Popped{entries,below}:
      S.bind(Rowing,List<&2,Entry>,rows_from(mode,words,entries),rowing => case_done(rowing,default,below,at,type_id,slot,scrutinee,mode))

def case_split(split: Split, stack: List<&2,Entry>, +at: U32, +type_id: U32, +slot: U32, +scrutinee: U32, +mode: U32) -> Result<S.Error,List<&2,Entry>>:
  match split:
    case Split{+words,Con{+default,Nil{}}}:
      S.bind(Popped,List<&2,Entry>,pop(U32.to_nat(U32.add(count(arm_offsets(mode,words)),Bool.pick(U32,U32.is_eq(default,none()),0,1))),stack,Nil{}),popped =>
        case_after(popped,words,default,at,type_id,slot,scrutinee,mode))
    case _: malformed(List<&2,Entry>,"case length")

def case_operation(x: List<&2,U32>, +at: U32, +type_id: U32, stack: List<&2,Entry>) -> Result<S.Error,List<&2,Entry>>:
  match x:
    case Con{+slot,Con{+scrutinee,Con{+mode,Con{+n,+tail}}}}:
      S.choose(Result<S.Error,List<&2,Entry>>,Bool.and(U32.is_lt(mode,2),U32.is_le(n,count(tail))),u =>
        S.bind(Split,List<&2,Entry>,split_words(U32.to_nat(Bool.pick(U32,U32.is_eq(mode,0),n,U32.mul(n,2))),tail,Nil{}),split => case_split(split,stack,at,type_id,slot,scrutinee,mode)),u => malformed(List<&2,Entry>,"case length"))
    case _: malformed(List<&2,Entry>,"case length")

def operation(op: U32, x: List<&2,U32>, at: U32, type_id: U32, stack: List<&2,Entry>, constants: List<&2,Constant>) -> Result<S.Error,List<&2,Entry>>:
  match op:
    case 0: literal_operation(x,at,type_id,stack,constants)
    case 1: counted_operation(1,x,at,type_id,stack)
    case 2: default_operation(x,at,stack)
    case 3: scalar_operation(3,x,at,type_id,stack)
    case 4: counted_operation(4,x,at,type_id,stack)
    case 5: scalar_operation(5,x,at,type_id,stack)
    case 6: counted_operation(6,x,at,type_id,stack)
    case 7: let_operation(x,at,type_id,stack)
    case 8: case_operation(x,at,type_id,stack)
    case 9: branch_operation(x,at,stack)
    case 10: closure_operation(x,at,type_id,stack)
    case 11: invoke_operation(x,at,type_id,stack)
    case 12: counted_operation(12,x,at,type_id,stack)
    case _: malformed(List<&2,Entry>,"opcode")

def nodes_from(records: List<&2,Located>, stack: List<&2,Entry>, +constants: List<&2,Constant>) -> Result<S.Error,List<&2,Entry>>:
  match records:
    case Nil{}: Done{stack}
    case Con{Located{at,Con{op,Con{type_id,x}}},tail}:
      S.bind(List<&2,Entry>,List<&2,Entry>,operation(op,x,at,type_id,stack,constants),next => nodes_from(tail,next,constants))
    case Con{other,tail}: malformed(List<&2,Entry>,"node record")

def functions_from(heads: List<&2,Head>, entries: List<&2,Entry>) -> Result<S.Error,List<&2,Function>>:
  match heads entries:
    case Nil{} Nil{}: Done{Nil{}}
    case Con{Head{name,result,slots,root,parameters},more} Con{Entry{+at,Whole{body}},later}:
      S.choose(Result<S.Error,List<&2,Function>>,U32.is_eq(at,root),u =>
        S.bind(List<&2,Function>,List<&2,Function>,functions_from(more,later),rest => Done{Con{Function{name,parameters,result,slots,body},rest}}),u => malformed(List<&2,Function>,"function root"))
    case _ _: malformed(List<&2,Function>,"unreachable node")

def planned(+functions: List<&2,Function>, shapes: List<&2,Shape>, +entry: U32, +main: U32, representation: List<&2,U32>) -> Result<S.Error,Plan>:
  S.choose(Result<S.Error,Plan>,U32.is_eq(main,main_index(functions,0)),u => Done{Plan{entry,representation,shapes,functions}},u => malformed(Plan,"main index"))

def assembled(entries: List<&2,Entry>, heads: List<&2,Head>, shaped: Shaped, +entry: U32, +main: U32, representation: List<&2,U32>) -> Result<S.Error,Plan>:
  match shaped:
    case Shaped{shapes,Nil{}}:
      S.bind(List<&2,Function>,Plan,functions_from(heads,entries),functions => planned(functions,shapes,entry,main,representation))
    case _: malformed(Plan,"constructor count")

def decode_nodes(stack: List<&2,Entry>, heads: List<&2,Head>, shaped: Shaped, +entry: U32, +main: U32, representation: List<&2,U32>) -> Result<S.Error,Plan>:
  assembled(List.reverse(&2,Entry,stack),heads,shaped,entry,main,representation)

def decode_stage(shaped: Shaped, heads: List<&2,Head>, nodes: List<&2,Located>, constants: List<&2,Constant>, +entry: U32, +main: U32, representation: List<&2,U32>) -> Result<S.Error,Plan>:
  S.bind(List<&2,Entry>,Plan,nodes_from(nodes,Nil{},constants),stack => decode_nodes(stack,heads,shaped,entry,main,representation))

def decode_constants_stage(constants: List<&2,Constant>, shaped: Shaped, heads: List<&2,Head>, nodes: List<&2,Located>, +entry: U32, +main: U32, representation: List<&2,U32>) -> Result<S.Error,Plan>:
  decode_stage(shaped,heads,nodes,constants,entry,main,representation)

def located_count(records: List<&2,Located>, +size: U32) -> U32:
  match records:
    case Nil{}: size
    case Con{head,tail}: located_count(tail,U32.add(size,1))

def decode_shapes_stage(+names: List<&2,String>, +types: List<&2,Located>, constructors: List<&2,Located>, functions: List<&2,Located>, constants: List<&2,Located>, nodes: List<&2,Located>,
    +entry: U32, +main: U32, representation: List<&2,U32>) -> Result<S.Error,Plan>:
  S.bind(Shaped,Plan,decode_shapes(U32.to_nat(U32.add(U32.mul(3,located_count(types,0)),2)),names,Next{types,constructors,0,0,Nil{}}),shaped =>
    S.bind(List<&2,Head>,Plan,decode_heads(functions,names),heads =>
      S.bind(List<&2,Constant>,Plan,decoded_constants(constants),pool => decode_constants_stage(pool,shaped,heads,nodes,entry,main,representation))))

def decode_sections(gathered: Gathered, +entry: U32, +main: U32, representation: List<&2,U32>) -> Result<S.Error,Plan>:
  match gathered:
    case Gathered{Con{types,Con{constructors,Con{functions,Con{constants,Con{nodes,Con{names,Nil{}}}}}}},Nil{},at}:
      S.bind(List<&2,String>,Plan,decoded_names(names,Nil{}),listed => decode_shapes_stage(listed,types,constructors,functions,constants,nodes,entry,main,representation))
    case Gathered{sections,Nil{},at}: malformed(Plan,"sections")
    case Gathered{sections,rest,at}: malformed(Plan,"trailing words")

def decode_body(header: Header, rest: List<&2,U32>, +total_words: U32) -> Result<S.Error,Plan>:
  match header:
    case Header{+total,+entry,+main,+offsets,+representation}:
      S.choose(Result<S.Error,Plan>,U32.is_eq(total,total_words),u =>
        S.bind(Gathered,Plan,read_sections(16n,offsets,Fresh{rest,32,Nil{}}),gathered => decode_sections(gathered,entry,main,representation)),u => malformed(Plan,"total"))

def decode_split(split: Split, +total_words: U32) -> Result<S.Error,Plan>:
  match split:
    case Split{head,rest}: S.bind(Header,Plan,parsed_header(head),header => decode_body(header,rest,total_words))

# The words of an image, back to its plan. The size limit comes first, even for a malformed image.
def decode(+words: List<&2,U32>) -> Result<S.Error,Plan>:
  S.choose(Result<S.Error,Plan>,U32.is_gt(count(words),image_words()),u => exhausted(Plan),u =>
    S.bind(Split,Plan,split_words(32n,words,Nil{}),split => decode_split(split,count(words))))

# Bytes to words, little-endian: the input of `decode` from a file of `File.read_bytes`.
def words_onto(bytes: List<&2,U32>, acc: List<&2,U32>) -> Result<S.Error,List<&2,U32>>:
  match bytes:
    case Nil{}: Done{List.reverse(&2,U32,acc)}
    case Con{+a,Con{+b,Con{+c,Con{+d,tail}}}}:
      words_onto(tail,Con{U32.or(a,U32.or(U32.shln(b,8n),U32.or(U32.shln(c,16n),U32.shln(d,24n)))),acc})
    case _: malformed(List<&2,U32>,"length")

def words_of(bytes: List<&2,U32>) -> Result<S.Error,List<&2,U32>>:
  words_onto(bytes,Nil{})

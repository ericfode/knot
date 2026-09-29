import Base
import ./syntax.bend as S
import ./core.bend as C
import ./image-plan.bend as P
import ./image-layout.bend as Y
import ./image-decode.bend as X

# knot-image-1 (vm/SPEC.md), the encoder: a checked Book is erased to a Plan and laid out.
# `erase_tokens` is a projection, not a rewriting: tokens, quantity-0 binders, levels and datatype kinds do
# not survive. A form without an encoding is reported `Unsupported compile image-term`, a broken invariant
# `InternalFailure compile`; nothing unchecked passes through.

# A level is a binder of the checked core; a slot is its place among the live binders. An erased
# binder has no slot, and a live reference to it is an invariant break, not source Invalid.
type Local is Data:
  Local{level: U32, slot: U32, type_id: U32, live: Bool}

type Bound is Data:
  Bound{locals: List<&2,Local>, depth: U32}

type Lowered is Data:
  Lowered{nodes: List<&2,P.Node>, rows: List<&2,P.Row>, deepest: U32}

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
    case Nil{}: P.diagnostic(Local,"image-level")
    case Con{+head,+tail}:
      match head:
        case Local{id,slot,type_id,live}:
          S.choose(Result<S.Error,Local>,U32.is_eq(id,level),u => Done{head},u => lookup(tail,level))

def live_local(local: Local) -> Result<S.Error,Local>:
  match local:
    case Local{level,slot,type_id,+live}:
      S.choose(Result<S.Error,Local>,live,u => Done{Local{level,slot,type_id,live}},u => P.diagnostic(Local,"image-erased-reference"))

def function_at(functions: List<&2,C.Function>, +index: U32) -> Result<S.Error,C.Function>:
  match functions:
    case Nil{}: P.diagnostic(C.Function,"image-function")
    case Con{+head,+tail}:
      S.choose(Result<S.Error,C.Function>,U32.is_eq(index,0),u => Done{head},u => function_at(tail,U32.sub(index,1)))

def datatype_at(types: List<&2,C.Datatype>, +index: U32) -> Result<S.Error,C.Datatype>:
  match types:
    case Nil{}: P.diagnostic(C.Datatype,"image-type")
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
    case _: P.diagnostic(Lowered,"image-single")

def joined(head: Lowered, tail: Lowered) -> Result<S.Error,Lowered>:
  match head tail:
    case Lowered{Con{node,Nil{}},Nil{},+a} Lowered{nodes,rows,+b}: Done{Lowered{Con{node,nodes},rows,max_depth(a,b)}}
    case _ _: P.diagnostic(Lowered,"image-operand")

def prepend_row(head: Lowered, tail: Lowered) -> Result<S.Error,Lowered>:
  match head tail:
    case Lowered{Nil{},Con{row,Nil{}},+a} Lowered{nodes,rows,+b}: Done{Lowered{nodes,Con{row,rows},max_depth(a,b)}}
    case _ _: P.diagnostic(Lowered,"image-row")

def one(node: P.Node, deepest: U32) -> Lowered:
  Lowered{Con{node,Nil{}},Nil{},deepest}

# A constructor whose fields are all erased has no operand: the image spells it as a Value.
def constructed(operands: Lowered, +type_id: U32, +tag: U32) -> Result<S.Error,Lowered>:
  match operands:
    case Lowered{Nil{},rows,deepest}: Done{one(P.Value{type_id,tag},deepest)}
    case Lowered{nodes,rows,deepest}: Done{one(P.Construct{type_id,tag,nodes},deepest)}

def called(operands: Lowered, +type_id: U32, +index: U32) -> Result<S.Error,Lowered>:
  match operands:
    case Lowered{nodes,rows,deepest}: Done{one(P.Application{type_id,index,nodes},deepest)}

def referenced(local: Local, +depth: U32) -> Result<S.Error,Lowered>:
  match local:
    case Local{level,slot,type_id,live}: Done{one(P.Reference{type_id,slot},depth)}

# The Let's own type is its body's: a positional type, never the initializer's (SPEC section 3).
def bound_let(value: Lowered, body: Lowered, +slot: U32) -> Result<S.Error,Lowered>:
  match value body:
    case Lowered{Con{initial,Nil{}},Nil{},+a} Lowered{Con{+result,Nil{}},Nil{},+b}:
      Done{one(P.Let{P.type_of(result),slot,initial,result},max_depth(a,b))}
    case _ _: P.diagnostic(Lowered,"image-let")

def case_node(table: Lowered, +type_id: U32, +slot: U32, +scrutinee: U32) -> Result<S.Error,Lowered>:
  match table:
    case Lowered{Nil{},rows,deepest}: Done{one(P.Case{type_id,slot,scrutinee,0,rows,None{}},deepest)}
    case _: P.diagnostic(Lowered,"image-case")

def branch_row(body: Lowered, +key: U32, +first: U32, +fields: U32) -> Result<S.Error,Lowered>:
  match body:
    case Lowered{Con{node,Nil{}},Nil{},deepest}: Done{Lowered{Nil{},Con{P.Branch{key,first,fields,node},Nil{}},deepest}}
    case _: P.diagnostic(Lowered,"image-branch")

# The current base has no term that needs a wider encoding; each form below is exhaustive so that a
# new C.Term constructor cannot compile until it is encoded or refused here.
def lower(fuel: Nat, mode: Mode, +types: List<&2,C.Datatype>, +functions: List<&2,C.Function>, +locals: List<&2,Local>, +depth: U32) -> Result<S.Error,Lowered>:
  match fuel mode:
    case 0n _: Fail{S.Exhausted{"compile",S.At{0,0,0,0}}}
    case 1n+ +n Term{C.Value{token,+type_id,+tag}}: Done{one(P.Value{type_id,tag},depth)}
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
    case 1n+ +n Term{C.Branch{tag,fields,body}}: P.diagnostic(Lowered,"image-branch-node")
    case 1n+ +n Term{C.Sequence{items}}: P.diagnostic(Lowered,"image-sequence-node")
    case 1n+ +n Operands{Nil{},Nil{}}: Done{Lowered{Nil{},Nil{},depth}}
    case 1n+ +n Operands{Con{+head,+tail},Con{C.Parameter{token,+q,type_id},+rest}}:
      S.choose(Result<S.Error,Lowered>,U32.is_eq(q,0),u => lower(n,Operands{tail,rest},types,functions,locals,depth),u =>
        S.bind(Lowered,Lowered,lower(n,Term{head},types,functions,locals,depth),first =>
          S.bind(Lowered,Lowered,lower(n,Operands{tail,rest},types,functions,locals,depth),remaining => joined(first,remaining))))
    case 1n+ +n Operands{terms,parameters}: P.diagnostic(Lowered,"image-argument-arity")
    case 1n+ +n Table{arms,+tag,Nil{}}: Done{Lowered{Nil{},Nil{},depth}}
    case 1n+ +n Table{+arms,+tag,Con{constructor,+rest}}:
      S.bind(Lowered,Lowered,lower(n,Arm{arm_for(arms,tag),tag},types,functions,locals,depth),row =>
        S.bind(Lowered,Lowered,lower(n,Table{arms,U32.add(tag,1),rest},types,functions,locals,depth),remaining => prepend_row(row,remaining)))
    case 1n+ +n Arm{None{},key}: Done{Lowered{Nil{},Con{P.Missing{},Nil{}},depth}}
    case 1n+ +n Arm{Some{C.Branch{pattern,+fields,+body}},+key}:
      lower(n,Fields{field_locals(fields,depth,locals),body,key,live_bindings(fields)},types,functions,locals,depth)
    case 1n+ +n Arm{other,key}: P.diagnostic(Lowered,"image-arm-node")
    case 1n+ +n Bind{Lowered{Con{+node,Nil{}},Nil{},+a},+level,+body}:
      S.bind(Lowered,Lowered,lower(n,Term{body},types,functions,Con{Local{level,depth,P.type_of(node),True{}},locals},U32.add(depth,1)),inner =>
        bound_let(Lowered{Con{node,Nil{}},Nil{},a},inner,depth))
    case 1n+ +n Bind{value,level,body}: P.diagnostic(Lowered,"image-let")
    case 1n+ +n Scrutinee{Local{id,+slot,+scrutinee,live},+type_id,+arms}:
      S.bind(C.Datatype,Lowered,datatype_at(types,scrutinee),definition =>
        S.bind(Lowered,Lowered,lower(n,Table{arms,0,datatype_constructors(definition)},types,functions,locals,depth),table => case_node(table,type_id,slot,scrutinee)))
    case 1n+ +n Fields{Bound{extended,+inner},+body,+key,+count}:
      S.bind(Lowered,Lowered,lower(n,Term{body},types,functions,extended,inner),lowered =>
        branch_row(lowered,key,depth,count))

def constructor_plan(constructors: List<&2,C.Constructor>) -> List<&2,P.Constructor>:
  match constructors:
    case Nil{}: Nil{}
    case Con{C.Constructor{token,fields},tail}: Con{P.Constructor{S.text(token),live_types(fields)},constructor_plan(tail)}

def shape_plan(types: List<&2,C.Datatype>) -> List<&2,P.Shape>:
  match types:
    case Nil{}: Nil{}
    case Con{C.Datatype{token,reusable,constructors},tail}: Con{P.Algebraic{S.text(token),constructor_plan(constructors)},shape_plan(tail)}

def function_done(lowered: Lowered, +name: String, +parameters: List<&2,U32>, +result: U32) -> Result<S.Error,P.Function>:
  match lowered:
    case Lowered{Con{node,Nil{}},Nil{},deepest}: Done{P.Function{name,parameters,result,deepest,node}}
    case _: P.diagnostic(P.Function,"image-body")

def function_lowered(fuel: Nat, bound: Bound, +body: C.Term, +name: String, +live: List<&2,U32>, +result: U32, +types: List<&2,C.Datatype>, +functions: List<&2,C.Function>) -> Result<S.Error,P.Function>:
  match bound:
    case Bound{locals,depth}:
      S.bind(Lowered,P.Function,lower(fuel,Term{body},types,functions,locals,depth),lowered => function_done(lowered,name,live,result))

def function_plan(fuel: Nat, function: C.Function, +types: List<&2,C.Datatype>, +functions: List<&2,C.Function>) -> Result<S.Error,P.Function>:
  match function:
    case C.Function{C.Signature{token,+parameters,+result},+body}:
      function_lowered(fuel,parameter_locals(parameters,0,0,Nil{}),body,S.text(token),live_types(parameters),result,types,functions)

def function_plans(+fuel: Nat, remaining: List<&2,C.Function>, +types: List<&2,C.Datatype>, +functions: List<&2,C.Function>) -> Result<S.Error,List<&2,P.Function>>:
  match remaining:
    case Nil{}: Done{Nil{}}
    case Con{+head,tail}:
      S.bind(P.Function,List<&2,P.Function>,function_plan(fuel,head,types,functions),first =>
        S.bind(List<&2,P.Function>,List<&2,P.Function>,function_plans(fuel,tail,types,functions),rest => Done{Con{first,rest}}))

# Nat, U32, Char, String, Bool, Cmp, Unit, List, Result, Sigma, IO.OP and File are pinned by a Base
# import, which this base does not accept: no representation type is declared.
def undeclared() -> List<&2,U32>:
  [P.none(),P.none(),P.none(),P.none(),P.none(),P.none(),P.none(),P.none(),P.none(),P.none(),P.none(),P.none()]

# The plan of a checked book: tokens, quantity-0 binders, levels and datatype kinds do not survive.
def erase_tokens(fuel: Nat, book: C.Book) -> Result<S.Error,P.Plan>:
  match book:
    case C.Book{+types,+functions}:
      S.bind(List<&2,P.Function>,P.Plan,function_plans(fuel,functions,types,functions),planned => Done{P.Plan{0,undeclared(),shape_plan(types),planned}})

# ---------------------------------------------------------------- layout

def encode(+fuel: Nat, book: C.Book) -> Result<S.Error,Y.Encoded>:
  S.bind(P.Plan,Y.Encoded,erase_tokens(fuel,book),plan => Y.layout(fuel,plan))

# ---------------------------------------------------------------- byte stream

def flatten(encoded: Y.Encoded) -> List<&2,U32>:
  match encoded:
    case Y.Encoded{records,words}: List.concat(&2,U32,records)

def decoded_image(result: Result<S.Error,Y.Encoded>) -> Result<S.Error,P.Plan>:
  match result:
    case Fail{e}: Fail{e}
    case Done{encoded}: X.decode(flatten(encoded))

# What decoding the words of a book's image gives. The round-trip law says it is the book's erased plan.
def recoded(fuel: Nat, book: C.Book) -> Result<S.Error,P.Plan>:
  decoded_image(encode(fuel,book))

import Base
import ./word.bend as W
import ./decode.bend as D

# ---------------------------------------------------------------- registry

# Representation positions follow header words 12-23.
def rep_name(+r: U32) -> String:
  D.nth_text(["Nat","U32","Char","String","Bool","Cmp","Unit","List","Result","Sigma","IO.OP","File"],r)

type Primitive is Data:
  Primitive{inputs: List<&2,U32>, output: U32}

def primitive_at(table: List<&2,Primitive>, +id: U32) -> Maybe<&2,Primitive>:
  match table:
    case Nil{}: None{}
    case Con{+p,+rest}: W.choose(Maybe<&2,Primitive>,U32.is_eq(id,0),u => Some{p},u => primitive_at(rest,U32.sub(id,1)))

# registry.json ids 0..38 in order, inputs and output as representation
# positions; 39 and 40 are reserved and absent.
def prims() -> List<&2,Primitive>:
  [Primitive{[1,1],1},Primitive{[1,1],1},Primitive{[1,1],1},Primitive{[1,1],1},Primitive{[1,1],1},Primitive{[1],1},Primitive{[1,1],1},
   Primitive{[1,1],5},Primitive{[1,1],4},Primitive{[1,1],4},Primitive{[1,1],4},Primitive{[1,1],4},Primitive{[1,1],4},Primitive{[1,1],4},
   Primitive{[1,0],1},Primitive{[1,0],1},Primitive{[1],0},Primitive{[0],1},Primitive{[1],2},Primitive{[2],1},
   Primitive{[2,2],4},Primitive{[2],4},
   Primitive{[0,0],0},Primitive{[0,0],0},Primitive{[0,0],0},Primitive{[0,0],5},
   Primitive{[0,0],4},Primitive{[0,0],4},Primitive{[0,0],4},Primitive{[0,0],4},Primitive{[0,0],4},Primitive{[0,0],4},
   Primitive{[1],3},Primitive{[0],3},Primitive{[3,3],4},Primitive{[3,3],3},Primitive{[3],3},Primitive{[3],0},Primitive{[3],4}]

def foreigns() -> List<&2,Primitive>:
  [Primitive{[],7},Primitive{[3],6},Primitive{[3,3],8},Primitive{[11,1],9},
   Primitive{[11,7],9},Primitive{[11],6},Primitive{[11,1],9},Primitive{[3],8}]

def nth_fields(xs: List<&2,List<&2,List<&2,U32>>>, +i: U32) -> List<&2,List<&2,U32>>:
  match xs:
    case Nil{}: Nil{}
    case Con{+x,+rest}: W.choose(List<&2,List<&2,U32>>,U32.is_eq(i,0),u => x,u => nth_fields(rest,U32.sub(i,1)))

# Pinned live field types by constructor: a representation position, or none
# for an erased type parameter. U32 and File are opaque and have no row.
def pinned(+r: U32) -> List<&2,List<&2,U32>>:
  +o = W.none()
  nth_fields([[[],[0]],[],[[1]],[[],[2,3]],[[],[]],[[],[],[]],[[]],[[],[o,7]],[[o],[o]],[[o,o]],[[o],[1,3]],[]],r)

# ---------------------------------------------------------------- validation

def nth_sort(types: List<&2,W.Sort>, +t: U32) -> Maybe<&2,W.Sort>:
  match types:
    case Nil{}: None{}
    case Con{+s,+rest}: W.choose(Maybe<&2,W.Sort>,U32.is_eq(t,0),u => Some{s},u => nth_sort(rest,U32.sub(t,1)))

# Kind codes of SPEC §2: 0 algebraic, 1 live arrow, 2 erased arrow, 3 opaque.
def sort_code(sort: Maybe<&2,W.Sort>) -> U32:
  match sort:
    case None{}: W.none()
    case Some{W.Algebraic{name,cs}}: 0
    case Some{W.Arrow{d,r}}: 1
    case Some{W.Erased{d,r}}: 2
    case Some{W.Opaque{name}}: 3

def kind(+types: List<&2,W.Sort>, +t: U32) -> U32:
  sort_code(nth_sort(types,t))

def sort_constructors(sort: Maybe<&2,W.Sort>) -> List<&2,W.Constructor>:
  match sort:
    case Some{W.Algebraic{name,cs}}: cs
    case _: Nil{}

def constructors_of(+types: List<&2,W.Sort>, +t: U32) -> List<&2,W.Constructor>:
  sort_constructors(nth_sort(types,t))

def sort_domain(sort: Maybe<&2,W.Sort>) -> U32:
  match sort:
    case Some{W.Arrow{d,r}}: d
    case Some{W.Erased{d,r}}: d
    case _: W.none()

def sort_result(sort: Maybe<&2,W.Sort>) -> U32:
  match sort:
    case Some{W.Arrow{d,r}}: r
    case Some{W.Erased{d,r}}: r
    case _: W.none()

def domain(+types: List<&2,W.Sort>, +t: U32) -> U32:
  sort_domain(nth_sort(types,t))

def codomain(+types: List<&2,W.Sort>, +t: U32) -> U32:
  sort_result(nth_sort(types,t))

def fields_of(constructors: List<&2,W.Constructor>, +tag: U32) -> List<&2,U32>:
  match constructors:
    case Nil{}: Nil{}
    case Con{W.Constructor{name,+fields},+rest}: W.choose(List<&2,U32>,U32.is_eq(tag,0),u => fields,u => fields_of(rest,U32.sub(tag,1)))

def is_arrow(+k: U32) -> Bool:
  W.or(U32.is_eq(k,1),U32.is_eq(k,2))

# `actual` may flow site `declared` is expected: none fits any type, and arrows
# of one kind fit position by position (SPEC §3).
def fits(fuel: Nat, +types: List<&2,W.Sort>, +declared: U32, +actual: U32) -> Bool:
  match fuel:
    case 0n: False{}
    case 1n+ +f:
      W.choose(Bool,W.or(W.or(W.is_none(declared),W.is_none(actual)),U32.is_eq(declared,actual)),u => True{},u =>
      W.choose(Bool,Bool.and(is_arrow(kind(types,declared)),U32.is_eq(kind(types,declared),kind(types,actual))),u =>
        Bool.and(fits(f,types,domain(types,declared),domain(types,actual)),fits(f,types,codomain(types,declared),codomain(types,actual))),
        u => False{}))

def fit(+types: List<&2,W.Sort>, +declared: U32, +actual: U32) -> Bool:
  fits(U32.to_nat(U32.add(W.count(W.Sort,types),1)),types,declared,actual)

# t is IO(x) = @-R: Type -> (x -> IO.OP<R>) -> IO.OP<R>, with x concrete (SPEC §8).
def is_io(+types: List<&2,W.Sort>, +op: U32, +t: U32, +x: U32) -> Bool:
  +live = codomain(types,t)
  +k = domain(types,live)
  Bool.and(Bool.and(Bool.not(W.is_none(x)),Bool.not(W.is_none(op))),
  Bool.and(Bool.and(U32.is_eq(kind(types,t),2),W.is_none(domain(types,t))),
  Bool.and(Bool.and(U32.is_eq(kind(types,live),1),U32.is_eq(codomain(types,live),op)),
  Bool.and(U32.is_eq(kind(types,k),1),Bool.and(U32.is_eq(domain(types,k),x),U32.is_eq(codomain(types,k),op))))))

type Context is Data:
  Context{types: List<&2,W.Sort>, functions: List<&2,W.Function>, representation: List<&2,U32>}

# An obligation of SPEC §4: check a node in a scope, check a closure or
# function body against its exact slot count, or refuse when `bad`.
type Task is Data:
  Check{node: W.Node, scope: List<&2,U32>, site: String}
  Nested{node: W.Node, scope: List<&2,U32>, site: String, slots: U32, owner: String, exact: Bool, fitted: Bool}
  Expect{bad: Bool, message: String}

def at_where(+site: String, what: String) -> String:
  String.concat([site,": ",what])

def type_of(node: W.Node) -> U32:
  match node:
    case W.Literal{t,c}: t
    case W.Intrinsic{t,p,xs}: t
    case W.Value{t,tag}: t
    case W.Construct{t,tag,xs}: t
    case W.Reference{t,slot}: t
    case W.Application{t,f,xs}: t
    case W.Let{t,slot,value,body}: t
    case W.Case{t,slot,s,mode,rows,d}: t
    case W.Closure{t,live,slots,cs,body}: t
    case W.Invoke{t,f,xs}: t
    case W.Foreign{t,id,xs}: t
    case _: W.none()

def types_of_nodes(nodes: List<&2,W.Node>) -> List<&2,U32>:
  match nodes:
    case Nil{}: Nil{}
    case Con{node,rest}: Con{type_of(node),types_of_nodes(rest)}

def checked(nodes: List<&2,W.Node>, +scope: List<&2,U32>, +site: String) -> List<&2,Task>:
  match nodes:
    case Nil{}: Nil{}
    case Con{node,rest}: Con{Check{node,scope,site},checked(rest,scope,site)}

def all_fit(+types: List<&2,W.Sort>, declared: List<&2,U32>, actual: List<&2,U32>) -> Bool:
  match declared actual:
    case Con{d,ds} Con{a,as}: Bool.and(fit(types,d,a),all_fit(types,ds,as))
    case _ _: True{}

# Operand r of a prim or foreign is the pinned representation `reps[r]`.
def pinned_operands(+reps: List<&2,U32>, +op: String, +site: String, actual: List<&2,U32>, inputs: List<&2,U32>) -> List<&2,Task>:
  match actual inputs:
    case Con{+a,as} Con{+r,rs}:
      Con{Expect{W.or(W.is_none(W.nth(reps,r)),Bool.not(U32.is_eq(a,W.nth(reps,r)))),at_where(site,String.concat([op," operand is not the pinned ",rep_name(r)]))},
        pinned_operands(reps,op,site,as,rs)}
    case _ _: Nil{}

def primitive_tasks(+cx: Context, +op: String, +id: U32, +t: U32, +site: String, +actual: List<&2,U32>, entry: Maybe<&2,Primitive>) -> List<&2,Task>:
  match cx entry:
    case _ None{}: [Expect{True{},at_where(site,String.concat(["unknown ",op," id ",U32.show(id)]))}]
    case Context{+types,functions,+reps} Some{Primitive{+inputs,+output}}:
      Con{Expect{Bool.not(U32.is_eq(W.count(U32,actual),W.count(U32,inputs))),at_where(site,String.append(op," arity"))},
        List.append(&2,Task,pinned_operands(reps,op,site,actual,inputs),
          W.choose(List<&2,Task>,String.eq(op,"prim"),
            u => [Expect{W.or(W.is_none(W.nth(reps,output)),Bool.not(U32.is_eq(t,W.nth(reps,output)))),at_where(site,String.append("prim result is not the pinned ",rep_name(output)))}],
            u => [Expect{Bool.not(is_io(types,W.nth(reps,10),t,W.nth(reps,output))),at_where(site,String.concat(["foreign result is not IO(",rep_name(output),")"]))}]))}

# Each word above the one before it. Keys span every u32, 0xffffffff included
# (SPEC §2); only captures are bounded, by the depth they are taken at.
def ascending(xs: List<&2,U32>, +floor: U32, +started: Bool) -> Bool:
  match xs:
    case Nil{}: True{}
    case Con{+x,rest}: Bool.and(W.or(Bool.not(started),U32.is_gt(x,floor)),ascending(rest,x,True{}))

def increasing(xs: List<&2,U32>) -> Bool:
  ascending(xs,0,False{})

def below(xs: List<&2,U32>, +bound: U32) -> Bool:
  match xs:
    case Nil{}: True{}
    case Con{+x,rest}: Bool.and(U32.is_lt(x,bound),below(rest,bound))

def scoped(caps: List<&2,U32>, +scope: List<&2,U32>) -> List<&2,U32>:
  match caps:
    case Nil{}: Nil{}
    case Con{c,rest}: Con{W.nth(scope,c),scoped(rest,scope)}

def row_nodes(rows: List<&2,Maybe<&2,W.Node>>) -> List<&2,W.Node>:
  match rows:
    case Nil{}: Nil{}
    case Con{None{},rest}: row_nodes(rest)
    case Con{Some{node},rest}: Con{node,row_nodes(rest)}

def uses_of(node: W.Node) -> List<&2,U32>:
  match node:
    case W.Reference{t,slot}: [slot]
    case W.Case{t,slot,s,mode,rows,d}: [slot]
    case W.Closure{t,live,slots,caps,body}: caps
    case _: Nil{}

def parts(node: W.Node) -> List<&2,W.Node>:
  match node:
    case W.Intrinsic{t,p,xs}: xs
    case W.Default{body}: [body]
    case W.Construct{t,tag,xs}: xs
    case W.Application{t,f,xs}: xs
    case W.Let{t,slot,value,body}: [value,body]
    case W.Case{t,slot,s,mode,+rows,d}: List.append(&2,W.Node,row_nodes(rows),row_nodes([d]))
    case W.Branch{key,first,fields,body}: [body]
    case W.Invoke{t,f,xs}: Con{f,xs}
    case W.Foreign{t,id,xs}: xs
    case _: Nil{}

# Slots a body reads directly: references, Case scrutinees and captures of the
# closures it builds, whose own bodies number their slots afresh.
def uses(fuel: Nat, nodes: List<&2,W.Node>) -> List<&2,U32>:
  match fuel nodes:
    case 1n+ +f Con{+node,rest}: List.append(&2,U32,uses_of(node),List.append(&2,U32,uses(f,parts(node)),uses(f,rest)))
    case _ _: Nil{}

def covers(n: Nat, +used: List<&2,U32>, +i: U32) -> Bool:
  match n:
    case 0n: True{}
    case 1n+m: Bool.and(W.member(used,i),covers(m,used,U32.add(i,1)))

def first_rep(reps: List<&2,U32>, +t: U32, +k: U32) -> U32:
  match reps:
    case Nil{}: W.none()
    case Con{+r,rest}: W.choose(U32,Bool.and(Bool.not(W.is_none(r)),U32.is_eq(r,t)),u => k,u => first_rep(rest,t,U32.add(k,1)))

# Constant kinds 0 U32, 1 Nat, 2 Char, 3 String name representations 1, 0, 2, 3.
def constant_rep(+kind: U32) -> U32:
  W.nth([1,0,2,3],kind)

def const_name(+kind: U32) -> String:
  D.nth_text(["U32","Nat","Char","String"],kind)

# Every arm body fits its Case, which has the type of the position it fills (SPEC §3).
def tag_tasks(rows: List<&2,Maybe<&2,W.Node>>, +types: List<&2,W.Sort>, +constructors: List<&2,W.Constructor>, +scope: List<&2,U32>, +depth: U32, +t: U32, +site: String, +tag: U32) -> List<&2,Task>:
  match rows:
    case Nil{}: Nil{}
    case Con{Some{W.Branch{+key,+first,+fields,+body}},rest}:
      +bound = fields_of(constructors,tag)
      List.append(&2,Task,
        [Expect{W.or(Bool.not(U32.is_eq(key,tag)),U32.is_ge(tag,W.count(W.Constructor,constructors))),at_where(site,"branch key")},
         Expect{W.or(Bool.not(U32.is_eq(first,depth)),Bool.not(U32.is_eq(fields,W.count(U32,bound)))),at_where(site,"branch binders")},
         Check{body,List.append(&2,U32,scope,bound),site},
         Expect{Bool.not(fit(types,t,type_of(body))),at_where(site,"branch body type")}],
        tag_tasks(rest,types,constructors,scope,depth,t,site,U32.add(tag,1)))
    case Con{row,rest}: tag_tasks(rest,types,constructors,scope,depth,t,site,U32.add(tag,1))

def key_tasks(rows: List<&2,Maybe<&2,W.Node>>, +types: List<&2,W.Sort>, +scope: List<&2,U32>, +depth: U32, +t: U32, +site: String) -> List<&2,Task>:
  match rows:
    case Con{Some{W.Branch{key,+first,+fields,+body}},rest}:
      List.append(&2,Task,
        [Expect{W.or(Bool.not(U32.is_eq(first,depth)),Bool.not(U32.is_eq(fields,0))),at_where(site,"key branch binds nothing")},
         Check{body,scope,site},
         Expect{Bool.not(fit(types,t,type_of(body))),at_where(site,"key branch body type")}],
        key_tasks(rest,types,scope,depth,t,site))
    case Con{row,rest}: key_tasks(rest,types,scope,depth,t,site)
    case Nil{}: Nil{}

def keys_of(rows: List<&2,Maybe<&2,W.Node>>) -> List<&2,U32>:
  match rows:
    case Con{Some{W.Branch{key,first,fields,body}},rest}: Con{key,keys_of(rest)}
    case Con{row,rest}: keys_of(rest)
    case Nil{}: Nil{}

def all_present(rows: List<&2,Maybe<&2,W.Node>>) -> Bool:
  match rows:
    case Nil{}: True{}
    case Con{None{},rest}: False{}
    case Con{Some{node},rest}: all_present(rest)

def default_tasks(fallback: Maybe<&2,W.Node>, +types: List<&2,W.Sort>, +scope: List<&2,U32>, +t: U32, +site: String) -> List<&2,Task>:
  match fallback:
    case Some{W.Default{+body}}: [Check{body,scope,site},Expect{Bool.not(fit(types,t,type_of(body))),at_where(site,"default body type")}]
    case _: Nil{}

def case_tasks(+cx: Context, +scope: List<&2,U32>, +depth: U32, +site: String, +t: U32, +scrutinee: U32, +mode: U32, +rows: List<&2,Maybe<&2,W.Node>>, +fallback: Maybe<&2,W.Node>) -> List<&2,Task>:
  match cx:
    case Context{+types,functions,+reps}:
      +constructors = constructors_of(types,scrutinee)
      List.append(&2,Task,W.choose(List<&2,Task>,U32.is_eq(mode,0),
        u => List.append(&2,Task,
          [Expect{Bool.not(U32.is_eq(kind(types,scrutinee),0)),at_where(site,"tag case on a non-data type")},
           Expect{Bool.not(U32.is_eq(W.count(Maybe<&2,W.Node>,rows),W.count(W.Constructor,constructors))),at_where(site,"tag table is not dense")},
           Expect{W.xor(Maybe.is_none(&2,W.Node,fallback),all_present(rows)),at_where(site,"default must cover exactly the missing tags")}],
          tag_tasks(rows,types,constructors,scope,depth,t,site,0)),
        u => List.append(&2,Task,
          [Expect{Bool.not(Bool.and(Bool.not(W.is_none(scrutinee)),W.or(U32.is_eq(scrutinee,W.nth(reps,1)),U32.is_eq(scrutinee,W.nth(reps,2))))),at_where(site,"key case on a non-scalar type")},
           Expect{W.or(Bool.not(increasing(keys_of(rows))),Maybe.is_none(&2,W.Node,fallback)),at_where(site,"keys must increase strictly, with a default")}],
          key_tasks(rows,types,scope,depth,t,site))),
        default_tasks(fallback,types,scope,t,site))

def callee(functions: List<&2,W.Function>, +f: U32) -> Maybe<&2,W.Function>:
  D.function_at(functions,f)

def callee_parameters(found: Maybe<&2,W.Function>) -> List<&2,U32>:
  match found:
    case Some{W.Function{name,parameters,result,slots,body}}: parameters
    case None{}: Nil{}

def callee_result(found: Maybe<&2,W.Function>) -> U32:
  match found:
    case Some{W.Function{name,parameters,result,slots,body}}: result
    case None{}: W.none()

def codes_text(codes: List<&2,U32>) -> String:
  match codes:
    case Nil{}: SNil{}
    case Con{c,rest}: SCon{Chr{c},codes_text(rest)}

def text_of(bytes: List<&2,U32>) -> String:
  codes_text(Maybe.default(&2,List<&2,U32>,W.scalars(bytes),Nil{}))

def type_index(+types: List<&2,W.Sort>, +t: U32, +site: String) -> Task:
  Expect{Bool.and(Bool.not(W.is_none(t)),U32.is_ge(t,W.count(W.Sort,types))),at_where(site,"type index")}

# A node's obligations in the reference validator's order: its own
# preconditions, its children, then what the children's types must satisfy.
def expand(+cx: Context, node: W.Node, +scope: List<&2,U32>, +depth: U32, +site: String) -> List<&2,Task>:
  match cx node:
    case Context{+types,+functions,+reps} W.Literal{+t,W.Constant{+k,data}}:
      [type_index(types,t,site),
       Expect{Bool.not(U32.is_eq(first_rep(reps,t,0),constant_rep(k))),at_where(site,String.concat([const_name(k)," literal at a non-",const_name(k)," type"]))}]
    case Context{+types,+functions,+reps} W.Value{+t,+tag}:
      [type_index(types,t,site),
       Expect{W.or(Bool.not(U32.is_eq(kind(types,t),0)),W.or(U32.is_ge(tag,W.count(W.Constructor,constructors_of(types,t))),Bool.not(U32.is_eq(W.count(U32,fields_of(constructors_of(types,t),tag)),0)))),
         at_where(site,"value is not a nullary constructor")}]
    case Context{+types,+functions,+reps} W.Reference{+t,+slot}:
      [type_index(types,t,site),
       Expect{U32.is_ge(slot,depth),at_where(site,String.concat(["slot ",U32.show(slot)," beyond depth ",U32.show(depth)]))},
       Expect{Bool.not(U32.is_eq(W.nth(scope,slot),t)),at_where(site,"reference type")}]
    case Context{+types,+functions,+reps} W.Construct{+t,+tag,+xs}:
      +fields = fields_of(constructors_of(types,t),tag)
      Con{type_index(types,t,site),List.append(&2,Task,checked(xs,scope,site),
        [Expect{W.or(Bool.not(U32.is_eq(kind(types,t),0)),U32.is_ge(tag,W.count(W.Constructor,constructors_of(types,t)))),at_where(site,"construct tag")},
         Expect{W.or(U32.is_eq(W.count(U32,fields),0),Bool.not(U32.is_eq(W.count(U32,fields),W.count(W.Node,xs)))),at_where(site,"construct arity")},
         Expect{Bool.not(all_fit(types,fields,types_of_nodes(xs))),at_where(site,"construct field type")}])}
    case Context{+types,+functions,+reps} W.Application{+t,+f,+xs}:
      +found = callee(functions,f)
      Con{type_index(types,t,site),List.append(&2,Task,checked(xs,scope,site),
        [Expect{U32.is_ge(f,W.count(W.Function,functions)),at_where(site,"function index")},
         Expect{Bool.not(U32.is_eq(W.count(W.Node,xs),W.count(U32,callee_parameters(found)))),at_where(site,"call arity")},
         Expect{Bool.not(Bool.and(fit(types,callee_result(found),t),all_fit(types,callee_parameters(found),types_of_nodes(xs)))),at_where(site,"call types")}])}
    case Context{+types,+functions,+reps} W.Intrinsic{+t,+id,+xs}:
      Con{type_index(types,t,site),List.append(&2,Task,checked(xs,scope,site),
        primitive_tasks(Context{types,functions,reps},"prim",id,t,site,types_of_nodes(xs),primitive_at(prims(),id)))}
    case Context{+types,+functions,+reps} W.Foreign{+t,+id,+xs}:
      Con{type_index(types,t,site),List.append(&2,Task,checked(xs,scope,site),
        primitive_tasks(Context{types,functions,reps},"foreign",id,t,site,types_of_nodes(xs),primitive_at(foreigns(),id)))}
    case Context{+types,+functions,+reps} W.Let{+t,+slot,+value,+body}:
      [type_index(types,t,site),
       Expect{Bool.not(U32.is_eq(slot,depth)),at_where(site,String.concat(["let slot ",U32.show(slot)," at depth ",U32.show(depth)]))},
       Check{value,scope,site},
       Check{body,List.append(&2,U32,scope,[type_of(value)]),site},
       Expect{Bool.not(U32.is_eq(type_of(body),t)),at_where(site,"let body type")}]
    case Context{+types,+functions,+reps} W.Case{+t,+slot,+scrutinee,+mode,+rows,+fallback}:
      # The scrutinee type is concrete; its slot may be an erased position (SPEC §3).
      +held = W.nth(scope,slot)
      Con{type_index(types,t,site),
      Con{Expect{U32.is_ge(slot,depth),at_where(site,"case slot beyond depth")},
      Con{Expect{W.or(W.is_none(scrutinee),Bool.not(W.or(W.is_none(held),U32.is_eq(held,scrutinee)))),at_where(site,"case scrutinee type")},
        case_tasks(Context{types,functions,reps},scope,depth,site,t,scrutinee,mode,rows,fallback)}}}
    case Context{+types,+functions,+reps} W.Closure{+t,+live,+slots,+caps,+body}:
      +arrow = kind(types,t)
      +inner = List.append(&2,U32,scoped(caps,scope),Bool.pick(List<&2,U32>,U32.is_eq(live,1),[domain(types,t)],Nil{}))
      [type_index(types,t,site),
       Expect{Bool.not(W.or(Bool.and(U32.is_eq(arrow,1),U32.is_eq(live,1)),Bool.and(U32.is_eq(arrow,2),U32.is_eq(live,0)))),at_where(site,"closure arrow")},
       Expect{Bool.not(Bool.and(increasing(caps),below(caps,depth))),at_where(site,"captures must increase strictly below depth")},
       Nested{body,inner,String.append(site,"/closure"),slots,site,
         covers(U32.to_nat(W.count(U32,caps)),uses(U32.to_nat(W.none()),[body]),0),fit(types,codomain(types,t),type_of(body))}]
    case Context{+types,+functions,+reps} W.Invoke{+t,+f,+xs}:
      +g = type_of(f)
      +arrow = kind(types,g)
      Con{type_index(types,t,site),Con{Check{f,scope,site},List.append(&2,Task,checked(xs,scope,site),
        [Expect{W.or(Bool.not(is_arrow(arrow)),Bool.not(U32.is_eq(W.count(W.Node,xs),Bool.pick(U32,U32.is_eq(arrow,1),1,0)))),at_where(site,"invoke arity")},
         Expect{W.or(Bool.not(fit(types,codomain(types,g),t)),Bool.and(Bool.not(U32.is_eq(W.count(W.Node,xs),0)),Bool.not(fit(types,domain(types,g),type_of(D.first(xs)))))),at_where(site,"invoke types")}])}}
    case _ W.Branch{key,first,fields,body}: [Expect{True{},at_where(site,"standalone branch")}]
    case _ W.Default{body}: [Expect{True{},at_where(site,"standalone default")}]

def larger(+a: U32, +b: U32) -> U32:
  Bool.pick(U32,U32.is_gt(a,b),a,b)

# Runs obligations in order; the first refused one is the reason. Returns the
# deepest scope reached, excluding nested closure bodies (SPEC §3).
def checks(fuel: Nat, tasks: List<&2,Task>, +cx: Context, +deepest: U32) -> Result<W.Stop,U32>:
  match fuel tasks:
    case _ Nil{}: Done{deepest}
    case 0n _: Fail{W.Refused{"image","validation depth"}}
    case 1n+ +f Con{Check{node,+scope,+site},rest}:
      W.then(U32,U32,checks(f,expand(cx,node,scope,W.count(U32,scope),site),cx,W.count(U32,scope)),+d =>
        checks(f,rest,cx,larger(deepest,d)))
    case 1n+ +f Con{Nested{node,+scope,inner,+slots,+owner,exact,fitted},rest}:
      W.then(U32,U32,checks(f,[Check{node,scope,inner}],cx,W.count(U32,scope)),+d =>
        W.unless(U32,Bool.not(exact),at_where(owner,"captures are not exactly the free slots of the body"),u =>
        W.unless(U32,Bool.not(U32.is_eq(d,slots)),at_where(owner,String.concat(["closure slots ",U32.show(slots),", reached ",U32.show(d)])),u =>
        W.unless(U32,Bool.not(fitted),at_where(owner,"closure result type"),u => checks(f,rest,cx,deepest)))))
    case 1n+ +f Con{Expect{bad,message},rest}:
      W.unless(U32,bad,message,u => checks(f,rest,cx,deepest))

def pin(+reps: List<&2,U32>, +spec: U32) -> U32:
  W.choose(U32,W.is_none(spec),u => W.none(),u => W.nth(reps,spec))

# A pinned field names a declared representation, or is an erased parameter.
def same_fields(+reps: List<&2,U32>, fields: List<&2,U32>, specs: List<&2,U32>) -> Bool:
  match fields specs:
    case Nil{} Nil{}: True{}
    case Con{+f,fs} Con{+s,ss}:
      Bool.and(Bool.and(U32.is_eq(f,pin(reps,s)),W.or(W.is_none(s),Bool.not(W.is_none(W.nth(reps,s))))),same_fields(reps,fs,ss))
    case _ _: False{}

def same_shape(+reps: List<&2,U32>, constructors: List<&2,W.Constructor>, specs: List<&2,List<&2,U32>>) -> Bool:
  match constructors specs:
    case Nil{} Nil{}: True{}
    case Con{W.Constructor{name,fields},cs} Con{s,ss}: Bool.and(same_fields(reps,fields,s),same_shape(reps,cs,ss))
    case _ _: False{}

def representations(n: Nat, +types: List<&2,W.Sort>, +reps: List<&2,U32>, +r: U32) -> Result<W.Stop,Unit>:
  match n:
    case 0n: Done{Unit{}}
    case 1n+ +m:
      +t = W.nth(reps,r)
      W.choose(Result<W.Stop,Unit>,W.is_none(t),u => representations(m,types,reps,U32.add(r,1)),u =>
      W.choose(Result<W.Stop,Unit>,W.or(U32.is_eq(r,1),U32.is_eq(r,11)),
        u => W.unless(Unit,Bool.not(U32.is_eq(kind(types,t),3)),String.concat(["representation: ",rep_name(r)," must be opaque"]),u =>
               representations(m,types,reps,U32.add(r,1))),
        u => W.unless(Unit,W.or(Bool.not(U32.is_eq(kind(types,t),0)),Bool.not(same_shape(reps,constructors_of(types,t),pinned(r)))),
               String.concat(["representation: ",rep_name(r)," shape"]),u => representations(m,types,reps,U32.add(r,1)))))

def function_names(functions: List<&2,W.Function>) -> List<&2,List<&2,U32>>:
  match functions:
    case Nil{}: Nil{}
    case Con{f,rest}: Con{D.name_of(f),function_names(rest)}


def grounded_at(+marks: List<&2,Bool>, +t: U32) -> Bool:
  W.or(W.is_none(t),W.nth_bool(marks,t))

def regrounded(sorts: List<&2,W.Sort>, +marks: List<&2,Bool>, current: List<&2,Bool>) -> List<&2,Bool>:
  match sorts current:
    case Con{W.Arrow{+d,+r},ss} Con{m,ms}: Con{W.or(m,Bool.and(grounded_at(marks,d),grounded_at(marks,r))),regrounded(ss,marks,ms)}
    case Con{W.Erased{+d,+r},ss} Con{m,ms}: Con{W.or(m,Bool.and(grounded_at(marks,d),grounded_at(marks,r))),regrounded(ss,marks,ms)}
    case Con{s,ss} Con{m,ms}: Con{m,regrounded(ss,marks,ms)}
    case _ _: Nil{}

def initial_ground(sorts: List<&2,W.Sort>) -> List<&2,Bool>:
  match sorts:
    case Nil{}: Nil{}
    case Con{W.Arrow{d,r},rest}: Con{False{},initial_ground(rest)}
    case Con{W.Erased{d,r},rest}: Con{False{},initial_ground(rest)}
    case Con{s,rest}: Con{True{},initial_ground(rest)}

def ground(n: Nat, +sorts: List<&2,W.Sort>, +marks: List<&2,Bool>) -> List<&2,Bool>:
  match n:
    case 0n: marks
    case 1n+m: ground(m,sorts,regrounded(sorts,marks,marks))

def every(xs: List<&2,Bool>) -> Bool:
  match xs:
    case Nil{}: True{}
    case Con{x,rest}: Bool.and(x,every(rest))

# Arrows are grounded once their domain and result are; a cycle never is.
def acyclic(+sorts: List<&2,W.Sort>) -> Bool:
  every(ground(U32.to_nat(U32.add(W.count(W.Sort,sorts),1)),sorts,initial_ground(sorts)))

def named_main(functions: List<&2,W.Function>) -> Maybe<&2,W.Function>:
  match functions:
    case Nil{}: None{}
    case Con{+f,+rest}: W.choose(Maybe<&2,W.Function>,W.same(D.name_of(f),D.main_bytes()),u => Some{f},u => named_main(rest))

def quoted(names: List<&2,String>) -> String:
  match names:
    case Nil{}: ""
    case Con{n,Nil{}}: String.concat(["'",n,"'"])
    case Con{n,rest}: String.concat(["'",n,"', ",quoted(rest)])

def missing(+reps: List<&2,U32>, wanted: List<&2,U32>) -> List<&2,String>:
  match wanted:
    case Nil{}: Nil{}
    case Con{+r,+rest}: W.choose(List<&2,String>,W.is_none(W.nth(reps,r)),u => Con{rep_name(r),missing(reps,rest)},u => missing(reps,rest))

def main_ready(found: Maybe<&2,W.Function>) -> Bool:
  match found:
    case Some{W.Function{name,parameters,result,slots,body}}: U32.is_eq(W.count(U32,parameters),0)
    case None{}: False{}

def main_returns(+types: List<&2,W.Sort>, +reps: List<&2,U32>, found: Maybe<&2,W.Function>) -> Bool:
  match found:
    case Some{W.Function{name,parameters,+result,slots,body}}: is_io(types,W.nth(reps,10),result,W.nth(reps,6))
    case None{}: True{}

# A Program's main takes no live argument and returns IO(Unit) (SPEC §8).
def program_valid(+entry: U32, +cx: Context) -> Result<W.Stop,Unit>:
  match cx:
    case Context{+types,+functions,+reps}:
      +absent = missing(reps,[6,3,10])
      W.choose(Result<W.Stop,Unit>,Bool.not(U32.is_eq(entry,1)),u => Done{Unit{}},u =>
      W.unless(Unit,Bool.not(main_ready(named_main(functions))),"program: main must exist with no live parameters",u =>
      W.unless(Unit,Bool.not(U32.is_eq(W.count(String,absent),0)),String.concat(["program: missing representation [",quoted(absent),"]"]),u =>
      W.unless(Unit,Bool.not(main_returns(types,reps,named_main(functions))),"program: main must return IO(Unit)",u => Done{Unit{}}))))

def types_in(cx: Context) -> List<&2,W.Sort>:
  match cx:
    case Context{types,functions,reps}: types

def function_valid(+cx: Context, f: W.Function) -> Result<W.Stop,Unit>:
  match f:
    case W.Function{name,+parameters,+result,+slots,+body}:
      +site = text_of(name)
      W.then(U32,Unit,checks(U32.to_nat(W.none()),[Check{body,parameters,site}],cx,W.count(U32,parameters)),+d =>
      W.unless(Unit,Bool.not(U32.is_eq(d,slots)),at_where(site,String.concat(["slots ",U32.show(slots),", reached ",U32.show(d)])),u =>
      W.unless(Unit,Bool.not(fit(types_in(cx),result,type_of(body))),at_where(site,"body type"),u => Done{Unit{}})))

def functions_valid(functions: List<&2,W.Function>, +cx: Context) -> Result<W.Stop,Unit>:
  match functions:
    case Nil{}: Done{Unit{}}
    case Con{f,rest}: W.then(Unit,Unit,function_valid(cx,f),u => functions_valid(rest,cx))

# SPEC §4 rules 4 and 5 on a decoded plan: representations, names, arrows,
# the Program entry, then every function, reachable or not.
def validate(plan: W.Plan) -> Result<W.Stop,Unit>:
  match plan:
    case W.Plan{+entry,+types,+functions,+reps}:
      +cx : Context = Context{types,functions,reps}
      W.then(Unit,Unit,representations(12n,types,reps,0),u =>
      W.unless(Unit,D.repeated(function_names(functions)),"functions: duplicate function name",u =>
      W.unless(Unit,Bool.not(acyclic(types)),"types: arrow cycle",u =>
      W.then(Unit,Unit,program_valid(entry,cx),u => functions_valid(functions,cx)))))

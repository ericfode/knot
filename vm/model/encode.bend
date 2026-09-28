import Base
import ./word.bend as W
import ./decode.bend as D
import ./validate.bend as V

# ---------------------------------------------------------------- encoding

def subtrees(node: W.Node) -> List<&2,W.Node>:
  match node:
    case W.Closure{t,live,slots,caps,body}: [body]
    case _: V.parts(node)

def record_size(node: W.Node) -> U32:
  match node:
    case W.Intrinsic{t,p,xs}: U32.add(5,W.count(W.Node,xs))
    case W.Construct{t,tag,xs}: U32.add(5,W.count(W.Node,xs))
    case W.Application{t,f,xs}: U32.add(5,W.count(W.Node,xs))
    case W.Foreign{t,id,xs}: U32.add(5,W.count(W.Node,xs))
    case W.Invoke{t,f,xs}: U32.add(5,W.count(W.Node,xs))
    case W.Let{t,slot,v,b}: 6
    case W.Branch{key,first,fields,body}: 7
    case W.Case{t,slot,s,+mode,rows,d}: U32.add(8,U32.mul(W.count(Maybe<&2,W.Node>,rows),Bool.pick(U32,U32.is_eq(mode,0),1,2)))
    case W.Closure{t,live,slots,caps,body}: U32.add(8,W.count(U32,caps))
    case _: 4

# Words of the records of these subtrees, children before parents.
def size(fuel: Nat, nodes: List<&2,W.Node>) -> U32:
  match fuel nodes:
    case 1n+ +f Con{+node,rest}: U32.add(U32.add(record_size(node),size(f,subtrees(node))),size(f,rest))
    case _ _: 0

def is_closure(node: W.Node) -> U32:
  match node:
    case W.Closure{t,live,slots,caps,body}: 1
    case _: 0

def closures(fuel: Nat, nodes: List<&2,W.Node>) -> U32:
  match fuel nodes:
    case 1n+ +f Con{+node,rest}: U32.add(U32.add(is_closure(node),closures(f,subtrees(node))),closures(f,rest))
    case _ _: 0

def is_literal(node: W.Node) -> List<&2,W.Constant>:
  match node:
    case W.Literal{t,c}: [c]
    case _: Nil{}

# Literal constants in node-stream order, repeats included.
def literals(fuel: Nat, nodes: List<&2,W.Node>) -> List<&2,W.Constant>:
  match fuel nodes:
    case 1n+ +f Con{+node,rest}: List.append(&2,W.Constant,List.append(&2,W.Constant,literals(f,subtrees(node)),is_literal(node)),literals(f,rest))
    case _ _: Nil{}

def same_constant(a: W.Constant, b: W.Constant) -> Bool:
  match a b:
    case W.Constant{ka,da} W.Constant{kb,db}: Bool.and(U32.is_eq(ka,kb),W.same(da,db))

def constant_index(constants: List<&2,W.Constant>, +c: W.Constant, +i: U32) -> U32:
  match constants:
    case Nil{}: W.none()
    case Con{+k,rest}: W.choose(U32,same_constant(k,c),u => i,u => constant_index(rest,c,U32.add(i,1)))

def interned(constants: List<&2,W.Constant>, +seen: List<&2,W.Constant>) -> List<&2,W.Constant>:
  match constants:
    case Nil{}: List.reverse(&2,W.Constant,seen)
    case Con{+c,rest}: interned(rest,Bool.pick(List<&2,W.Constant>,W.is_none(constant_index(seen,c,0)),Con{c,seen},seen))

def root_offsets(fuel: Nat, nodes: List<&2,W.Node>, +start: U32) -> List<&2,U32>:
  match fuel nodes:
    case 1n+ +f Con{+node,rest}:
      +span = U32.add(size(f,subtrees(node)),record_size(node))
      Con{U32.add(start,size(f,subtrees(node))),root_offsets(f,rest,U32.add(start,span))}
    case _ _: Nil{}

def table(rows: List<&2,Maybe<&2,W.Node>>, offsets: List<&2,U32>) -> List<&2,U32>:
  match rows offsets:
    case Con{None{},rest} _: Con{W.none(),table(rest,offsets)}
    case Con{Some{node},rest} Con{o,os}: Con{o,table(rest,os)}
    case _ _: Nil{}

def keyed_table(rows: List<&2,Maybe<&2,W.Node>>, offsets: List<&2,U32>) -> List<&2,U32>:
  match rows offsets:
    case Con{Some{W.Branch{key,first,fields,body}},rest} Con{o,os}: Con{key,Con{o,keyed_table(rest,os)}}
    case _ _: Nil{}

def fallback_offset(d: Maybe<&2,W.Node>, +offsets: List<&2,U32>) -> U32:
  match d:
    case None{}: W.none()
    case Some{node}: W.nth(offsets,U32.sub(W.count(U32,offsets),1))

# The record of one node whose children start at `start` and whose closures
# before it number `site`; an arm records its Case's type.
def own(node: W.Node, +offsets: List<&2,U32>, +site: U32, +arm: U32, +constants: List<&2,W.Constant>) -> List<&2,U32>:
  match node:
    case W.Literal{t,+c}: [4,0,t,constant_index(constants,c,0)]
    case W.Intrinsic{t,p,+xs}: Con{U32.add(5,W.count(W.Node,xs)),Con{1,Con{t,Con{p,Con{W.count(W.Node,xs),offsets}}}}}
    case W.Default{body}: [4,2,arm,W.nth(offsets,0)]
    case W.Value{t,tag}: [4,3,t,tag]
    case W.Construct{t,tag,+xs}: Con{U32.add(5,W.count(W.Node,xs)),Con{4,Con{t,Con{tag,Con{W.count(W.Node,xs),offsets}}}}}
    case W.Reference{t,slot}: [4,5,t,slot]
    case W.Application{t,g,+xs}: Con{U32.add(5,W.count(W.Node,xs)),Con{6,Con{t,Con{g,Con{W.count(W.Node,xs),offsets}}}}}
    case W.Let{t,slot,v,b}: [6,7,t,slot,W.nth(offsets,0),W.nth(offsets,1)]
    case W.Case{t,slot,s,+mode,+rows,+d}:
      +n = W.count(Maybe<&2,W.Node>,rows)
      Con{U32.add(8,U32.mul(n,Bool.pick(U32,U32.is_eq(mode,0),1,2))),Con{8,Con{t,Con{slot,Con{s,Con{mode,Con{n,
        List.append(&2,U32,W.choose(List<&2,U32>,U32.is_eq(mode,0),u => table(rows,offsets),u => keyed_table(rows,offsets)),[fallback_offset(d,offsets)])}}}}}}}
    case W.Branch{key,first,fields,body}: [7,9,arm,key,first,fields,W.nth(offsets,0)]
    case W.Closure{t,live,slots,+caps,body}:
      Con{U32.add(8,W.count(U32,caps)),Con{10,Con{t,Con{site,Con{live,Con{slots,Con{W.count(U32,caps),List.append(&2,U32,caps,[W.nth(offsets,0)])}}}}}}}
    case W.Invoke{t,g,+xs}: Con{U32.add(5,W.count(W.Node,xs)),Con{11,Con{t,Con{W.nth(offsets,0),Con{W.count(W.Node,xs),List.drop(&2,U32,offsets,1n)}}}}}
    case W.Foreign{t,id,+xs}: Con{U32.add(5,W.count(W.Node,xs)),Con{12,Con{t,Con{id,Con{W.count(W.Node,xs),offsets}}}}}

def arm_type(node: W.Node) -> U32:
  match node:
    case W.Case{t,slot,s,mode,rows,d}: t
    case _: W.none()

# Records of consecutive subtrees starting at `start`, post-order (SPEC §2).
def emit(fuel: Nat, nodes: List<&2,W.Node>, +start: U32, +site: U32, +arm: U32, +constants: List<&2,W.Constant>) -> List<&2,U32>:
  match fuel nodes:
    case 1n+ +f Con{+node,rest}:
      +kids = subtrees(node)
      +inner = U32.add(start,size(f,kids))
      List.append(&2,U32,List.append(&2,U32,emit(f,kids,start,site,arm_type(node),constants),
          own(node,root_offsets(f,kids,start),U32.add(site,closures(f,kids)),arm,constants)),
        emit(f,rest,U32.add(inner,record_size(node)),U32.add(site,closures(f,Con{node,Nil{}})),arm,constants))
    case _ _: Nil{}

def node_count(fuel: Nat, nodes: List<&2,W.Node>) -> U32:
  match fuel nodes:
    case 1n+ +f Con{+node,rest}: U32.add(U32.add(1,node_count(f,subtrees(node))),node_count(f,rest))
    case _ _: 0

def byte_index(names: List<&2,List<&2,U32>>, +x: List<&2,U32>, +i: U32) -> U32:
  match names:
    case Nil{}: W.none()
    case Con{+n,rest}: W.choose(U32,W.same(n,x),u => i,u => byte_index(rest,x,U32.add(i,1)))

def distinct(names: List<&2,List<&2,U32>>, +seen: List<&2,List<&2,U32>>) -> List<&2,List<&2,U32>>:
  match names:
    case Nil{}: List.reverse(&2,List<&2,U32>,seen)
    case Con{+n,rest}: distinct(rest,Bool.pick(List<&2,List<&2,U32>>,W.is_none(byte_index(seen,n,0)),Con{n,seen},seen))

def sort_names(sorts: List<&2,W.Sort>) -> List<&2,List<&2,U32>>:
  match sorts:
    case Nil{}: Nil{}
    case Con{W.Algebraic{name,cs},rest}: Con{name,sort_names(rest)}
    case Con{W.Opaque{name},rest}: Con{name,sort_names(rest)}
    case Con{s,rest}: sort_names(rest)

def constructor_list_names(cs: List<&2,W.Constructor>) -> List<&2,List<&2,U32>>:
  match cs:
    case Nil{}: Nil{}
    case Con{W.Constructor{name,fields},rest}: Con{name,constructor_list_names(rest)}

def constructor_names(sorts: List<&2,W.Sort>) -> List<&2,List<&2,U32>>:
  match sorts:
    case Nil{}: Nil{}
    case Con{W.Algebraic{name,cs},rest}: List.append(&2,List<&2,U32>,constructor_list_names(cs),constructor_names(rest))
    case Con{s,rest}: constructor_names(rest)

def type_records(sorts: List<&2,W.Sort>, +names: List<&2,List<&2,U32>>, +first: U32) -> List<&2,U32>:
  match sorts:
    case Nil{}: Nil{}
    case Con{W.Algebraic{+name,+cs},rest}: List.append(&2,U32,[5,0,byte_index(names,name,0),first,W.count(W.Constructor,cs)],type_records(rest,names,U32.add(first,W.count(W.Constructor,cs))))
    case Con{W.Opaque{+name},rest}: List.append(&2,U32,[5,3,byte_index(names,name,0),0,0],type_records(rest,names,first))
    case Con{W.Arrow{d,r},rest}: List.append(&2,U32,[5,1,W.none(),d,r],type_records(rest,names,first))
    case Con{W.Erased{d,r},rest}: List.append(&2,U32,[5,2,W.none(),d,r],type_records(rest,names,first))

def constructor_records(cs: List<&2,W.Constructor>, +names: List<&2,List<&2,U32>>, +t: U32, +tag: U32) -> List<&2,U32>:
  match cs:
    case Nil{}: Nil{}
    case Con{W.Constructor{+name,+fields},rest}:
      List.append(&2,U32,Con{U32.add(5,W.count(U32,fields)),Con{t,Con{tag,Con{byte_index(names,name,0),Con{W.count(U32,fields),fields}}}}},
        constructor_records(rest,names,t,U32.add(tag,1)))

def all_constructor_records(sorts: List<&2,W.Sort>, +names: List<&2,List<&2,U32>>, +t: U32) -> List<&2,U32>:
  match sorts:
    case Nil{}: Nil{}
    case Con{W.Algebraic{name,cs},rest}: List.append(&2,U32,constructor_records(cs,names,t,0),all_constructor_records(rest,names,U32.add(t,1)))
    case Con{s,rest}: all_constructor_records(rest,names,U32.add(t,1))

def body_of(f: W.Function) -> W.Node:
  match f:
    case W.Function{name,parameters,result,slots,body}: body

def bodies(functions: List<&2,W.Function>) -> List<&2,W.Node>:
  match functions:
    case Nil{}: Nil{}
    case Con{f,rest}: Con{body_of(f),bodies(rest)}

def function_records(functions: List<&2,W.Function>, +names: List<&2,List<&2,U32>>, roots: List<&2,U32>) -> List<&2,U32>:
  match functions roots:
    case Con{W.Function{+name,+parameters,result,slots,body},rest} Con{root,more}:
      List.append(&2,U32,Con{U32.add(6,W.count(U32,parameters)),Con{byte_index(names,name,0),Con{result,Con{W.count(U32,parameters),Con{slots,Con{root,parameters}}}}}},
        function_records(rest,names,more))
    case _ _: Nil{}

def constant_records(constants: List<&2,W.Constant>) -> List<&2,U32>:
  match constants:
    case Nil{}: Nil{}
    case Con{W.Constant{kind,+data},rest}: List.append(&2,U32,Con{U32.add(3,W.count(U32,data)),Con{kind,Con{W.count(U32,data),data}}},constant_records(rest))

def padded(+bytes: List<&2,U32>) -> List<&2,U32>:
  List.append(&2,U32,bytes,List.take(&2,U32,[0,0,0],U32.to_nat(U32.mod(U32.sub(4,U32.mod(W.count(U32,bytes),4)),4))))

def name_records(names: List<&2,List<&2,U32>>) -> List<&2,U32>:
  match names:
    case Nil{}: Nil{}
    case Con{+n,rest}:
      +packed = W.pack(padded(n))
      List.append(&2,U32,Con{U32.add(2,W.count(U32,packed)),Con{W.count(U32,n),packed}},name_records(rest))

def function_index(functions: List<&2,W.Function>, +x: List<&2,U32>, +i: U32) -> U32:
  match functions:
    case Nil{}: W.none()
    case Con{f,rest}: W.choose(U32,W.same(D.name_of(f),x),u => i,u => function_index(rest,x,U32.add(i,1)))

def parameter_lists(functions: List<&2,W.Function>) -> List<&2,List<&2,U32>>:
  match functions:
    case Nil{}: Nil{}
    case Con{W.Function{name,parameters,result,slots,body},rest}: Con{parameters,parameter_lists(rest)}

# The canonical layout of a plan (SPEC §2): names interned by first use over
# type, constructor and function names; constants by first use in the node
# stream; sections adjacent after the 32-word header.
def encode(plan: W.Plan) -> List<&2,U32>:
  match plan:
    case W.Plan{entry,+types,+functions,representation}:
      +fuel = U32.to_nat(W.none())
      +forest = bodies(functions)
      +names = distinct(List.append(&2,List<&2,U32>,sort_names(types),List.append(&2,List<&2,U32>,constructor_names(types),V.function_names(functions))),Nil{})
      +constants = interned(literals(fuel,forest),Nil{})
      +type_words : List<&2,U32> = Con{W.count(W.Sort,types),type_records(types,names,0)}
      +constructor_words : List<&2,U32> = Con{W.count(List<&2,U32>,constructor_names(types)),all_constructor_records(types,names,0)}
      +function_size = U32.add(1,U32.add(U32.mul(6,W.count(W.Function,functions)),W.count(U32,List.concat(&2,U32,parameter_lists(functions)))))
      +constant_words : List<&2,U32> = Con{W.count(W.Constant,constants),constant_records(constants)}
      +types_at : U32 = 32
      +constructors_at = U32.add(types_at,W.count(U32,type_words))
      +functions_at = U32.add(constructors_at,W.count(U32,constructor_words))
      +constants_at = U32.add(functions_at,function_size)
      +nodes_at = U32.add(constants_at,W.count(U32,constant_words))
      +node_words : List<&2,U32> = Con{node_count(fuel,forest),emit(fuel,forest,U32.add(nodes_at,1),0,W.none(),constants)}
      +names_at = U32.add(nodes_at,W.count(U32,node_words))
      +name_words : List<&2,U32> = Con{W.count(List<&2,U32>,names),name_records(names)}
      +function_words : List<&2,U32> = Con{W.count(W.Function,functions),function_records(functions,names,root_offsets(fuel,forest,U32.add(nodes_at,1)))}
      +total = U32.add(names_at,W.count(U32,name_words))
      List.concat(&2,U32,[[D.magic(),1,total,entry,function_index(functions,D.main_bytes(),0),types_at,constructors_at,functions_at,constants_at,nodes_at,names_at,0],
        representation,D.digest(),type_words,constructor_words,function_words,constant_words,node_words,name_words])

# ---------------------------------------------------------------- loading


def image_limit() -> U32:
  16777216

def refused(-A: Data, result: Result<String,A>) -> Result<W.Stop,A>:
  match result:
    case Fail{reason}: Fail{W.Refused{"image",reason}}
    case Done{value}: Done{value}

def validated(result: Result<String,Unit>) -> Result<String,Unit>:
  match result:
    case Fail{problem}: Fail{String.append("validator: ",problem)}
    case Done{u}: Done{u}

def admitted(+words: List<&2,U32>, +plan: W.Plan) -> Result<String,W.Plan>:
  W.then(Unit,W.Plan,validated(V.validate(plan)),u =>
    W.unless(W.Plan,Bool.not(W.same(encode(plan),words)),"noncanonical",u => Done{plan}))

# Words the loader admits: decoded, validated and canonical.
def admit(+words: List<&2,U32>) -> Result<W.Stop,W.Plan>:
  refused(W.Plan,W.then(W.Plan,W.Plan,D.decode(words),+plan => admitted(words,plan)))

# SPEC §4: size first, then the bytes, the plan's rules and canonicality. The
# loader never runs a body.
def load(+bytes: List<&2,U32>) -> Result<W.Stop,W.Plan>:
  +size = W.count(U32,bytes)
  W.choose(Result<W.Stop,W.Plan>,U32.is_gt(size,image_limit()),u => Fail{W.Exhausted{2,"image-size"}},u =>
  W.choose(Result<W.Stop,W.Plan>,W.or(Bool.not(U32.is_eq(U32.mod(size,4),0)),U32.is_lt(size,128)),u => Fail{W.Refused{"image","length"}},u =>
    admit(W.pack(bytes))))

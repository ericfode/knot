import Base
import ./syntax.bend as S
import ./image-plan.bend as P

# knot-image-1, layout: a Plan as words (names, tables, nodes with absolute offsets, header) and the
# chunked byte stream that a writer pulls.

def total_onto(records: List<&2,List<&2,U32>>, +size: U32) -> U32:
  match records:
    case Nil{}: size
    case Con{head,tail}: total_onto(tail,U32.add(size,P.count(head)))

def total(records: List<&2,List<&2,U32>>) -> U32:
  total_onto(records,0)

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

def shape_row(shape: P.Shape, rows: Records) -> Records:
  match shape rows:
    case P.Algebraic{name,constructors} Records{acc,names,first}:
      shaped(intern(names,name),acc,first,U32.from_nat(List.length(&2,P.Constructor,constructors)))
    case P.Arrow{domain,result} Records{acc,names,first}: Records{Con{[5,1,P.none(),domain,result],acc},names,first}
    case P.Erased{domain,result} Records{acc,names,first}: Records{Con{[5,2,P.none(),domain,result],acc},names,first}
    case P.Opaque{name} Records{acc,names,first}: opaque(intern(names,name),acc,first)

def shape_rows(shapes: List<&2,P.Shape>, rows: Records) -> Records:
  match shapes rows:
    case Nil{} Records{acc,names,next}: Records{List.reverse(&2,List<&2,U32>,acc),names,next}
    case Con{head,tail} Records{acc,names,next}: shape_rows(tail,shape_row(head,Records{acc,names,next}))

def constructor_named(named: Interned, +fields: List<&2,U32>, +type_index: U32, +tag: U32, acc: List<&2,List<&2,U32>>) -> Records:
  match named:
    case Interned{+index,names}: Records{Con{Con{U32.add(5,P.count(fields)),Con{type_index,Con{tag,Con{index,Con{P.count(fields),fields}}}}},acc},names,0}

def constructor_row(constructors: List<&2,P.Constructor>, +type_index: U32, +tag: U32, rows: Records) -> Records:
  match constructors rows:
    case Nil{} Records{acc,names,next}: Records{acc,names,next}
    case Con{P.Constructor{name,fields},tail} Records{acc,names,next}:
      constructor_row(tail,type_index,U32.add(tag,1),constructor_named(intern(names,name),fields,type_index,tag,acc))

def constructor_rows(shapes: List<&2,P.Shape>, +type_index: U32, rows: Records) -> Records:
  match shapes rows:
    case Nil{} Records{acc,names,next}: Records{List.reverse(&2,List<&2,U32>,acc),names,next}
    case Con{P.Algebraic{name,constructors},tail} Records{acc,names,next}:
      constructor_rows(tail,U32.add(type_index,1),constructor_row(constructors,type_index,0,Records{acc,names,next}))
    case Con{other,tail} Records{acc,names,next}: constructor_rows(tail,U32.add(type_index,1),Records{acc,names,next})

type Indexed is Data:
  Indexed{indices: List<&2,U32>, names: Names}

def indexed_name(named: Interned, acc: List<&2,U32>) -> Indexed:
  match named:
    case Interned{index,names}: Indexed{Con{index,acc},names}

def function_names(functions: List<&2,P.Function>, state: Indexed) -> Indexed:
  match functions state:
    case Nil{} Indexed{acc,names}: Indexed{List.reverse(&2,U32,acc),names}
    case Con{P.Function{name,parameters,result,slots,body},tail} Indexed{acc,names}:
      function_names(tail,indexed_name(intern(names,name),acc))

type Tables is Data:
  Tables{types: Records, constructors: Records, functions: Indexed}

def tables_finished(constructors: Records, types: Records, functions: List<&2,P.Function>) -> Tables:
  match constructors:
    case Records{acc,+names,next}: Tables{types,Records{acc,names,next},function_names(functions,Indexed{Nil{},names})}

def tables_named(types: Records, shapes: List<&2,P.Shape>, functions: List<&2,P.Function>) -> Tables:
  match types:
    case Records{acc,+names,next}: tables_finished(constructor_rows(shapes,0,Records{Nil{},names,0}),Records{acc,names,next},functions)

# Names, then constructor names, then function names, interned in that order (SPEC section 2).
def tables(+shapes: List<&2,P.Shape>, functions: List<&2,P.Function>) -> Tables:
  tables_named(shape_rows(shapes,Records{Nil{},Names{Nil{},0},0}),shapes,functions)

# ---------------------------------------------------------------- node records

# Records are numbered by their absolute word offset. `pool` and `records` hold the newest first.
type Nodes is Data:
  Nodes{records: List<&2,List<&2,U32>>, next: U32, pool: List<&2,P.Constant>, pooled: U32, sites: U32, nodes: U32}

type Placed is Data:
  Placed{offsets: List<&2,U32>, state: Nodes}

def same_constant(a: P.Constant, b: P.Constant) -> Bool:
  match a b:
    case P.Constant{+k,d} P.Constant{+l,e}: Bool.and(U32.is_eq(k,l),P.same_words(d,e))

def constant_at(pool: List<&2,P.Constant>, +constant: P.Constant, +top: U32) -> Maybe<&2,U32>:
  match pool:
    case Nil{}: None{}
    case Con{+head,+tail}:
      S.choose(Maybe<&2,U32>,same_constant(head,constant),u => Some{top},u => constant_at(tail,constant,U32.sub(top,1)))

def pooled_at(found: Maybe<&2,U32>, state: Nodes, +constant: P.Constant) -> Placed:
  match found state:
    case Some{index} Nodes{records,next,pool,pooled,sites,nodes}: Placed{Con{index,Nil{}},Nodes{records,next,pool,pooled,sites,nodes}}
    case None{} Nodes{records,next,pool,+pooled,sites,nodes}:
      Placed{Con{pooled,Nil{}},Nodes{records,next,Con{constant,pool},U32.add(pooled,1),sites,nodes}}

def constant_index(state: Nodes, +constant: P.Constant) -> Placed:
  match state:
    case Nodes{+records,+next,+pool,+pooled,+sites,+nodes}:
      pooled_at(constant_at(pool,constant,U32.sub(pooled,1)),Nodes{records,next,pool,pooled,sites,nodes},constant)

# A record is [length, opcode, result type, operands...]; its offset is the words before it.
def pushed(state: Nodes, +op: U32, +type_id: U32, +operands: List<&2,U32>) -> Result<S.Error,Placed>:
  match state:
    case Nodes{records,+next,pool,pooled,sites,+nodes}:
      S.choose(Result<S.Error,Placed>,U32.is_gt(next,P.image_words()),u => P.exhausted(Placed),u =>
        Done{Placed{Con{next,Nil{}},Nodes{Con{Con{U32.add(3,P.count(operands)),Con{op,Con{type_id,operands}}},records},U32.add(next,U32.add(3,P.count(operands))),pool,pooled,sites,U32.add(nodes,1)}}})

# [x, n, children...]: Intrinsic, Construct, Application and Foreign.
def counted(placed: Placed, +op: U32, +type_id: U32, +x: U32) -> Result<S.Error,Placed>:
  match placed:
    case Placed{+offsets,state}: pushed(state,op,type_id,Con{x,Con{P.count(offsets),offsets}})

def literal_node(indexed: Placed, +type_id: U32) -> Result<S.Error,Placed>:
  match indexed:
    case Placed{Con{index,Nil{}},state}: pushed(state,0,type_id,Con{index,Nil{}})
    case _: P.diagnostic(Placed,"image-literal")

def let_node(value: Placed, body: Placed, +type_id: U32, +slot: U32) -> Result<S.Error,Placed>:
  match value body:
    case Placed{Con{initial,Nil{}},before} Placed{Con{result,Nil{}},state}: pushed(state,7,type_id,[slot,initial,result])
    case _ _: P.diagnostic(Placed,"image-let")

def invoke_node(function: Placed, arguments: Placed, +type_id: U32) -> Result<S.Error,Placed>:
  match function arguments:
    case Placed{Con{callee,Nil{}},before} Placed{+offsets,state}: pushed(state,11,type_id,Con{callee,Con{P.count(offsets),offsets}})
    case _ _: P.diagnostic(Placed,"image-invoke")

def closure_node(body: Placed, +type_id: U32, +live: U32, +slots: U32, +captures: List<&2,U32>) -> Result<S.Error,Placed>:
  match body:
    case Placed{Con{child,Nil{}},Nodes{records,next,pool,pooled,+sites,nodes}}:
      pushed(Nodes{records,next,pool,pooled,U32.add(sites,1),nodes},10,type_id,Con{sites,Con{live,Con{slots,Con{P.count(captures),List.append(&2,U32,captures,Con{child,Nil{}})}}}})
    case _: P.diagnostic(Placed,"image-closure")

def default_node(body: Placed, +type_id: U32) -> Result<S.Error,Placed>:
  match body:
    case Placed{Con{child,Nil{}},state}: pushed(state,2,type_id,Con{child,Nil{}})
    case _: P.diagnostic(Placed,"image-default")

def joined_offsets(first: Placed, rest: Placed) -> Result<S.Error,Placed>:
  match first rest:
    case Placed{offsets,before} Placed{remaining,state}: Done{Placed{List.append(&2,U32,offsets,remaining),state}}

# A tag-mode row is one word: its Branch or `none`; a key-mode row is [key, Branch].
def row_words(placed: Placed, +key: U32, +mode: U32) -> Result<S.Error,Placed>:
  match placed:
    case Placed{Con{+at,Nil{}},state}:
      Done{Placed{S.choose(List<&2,U32>,U32.is_eq(mode,0),u => Con{at,Nil{}},u => Con{key,Con{at,Nil{}}}),state}}
    case _: P.diagnostic(Placed,"image-row")

def branch_node(body: Placed, +key: U32, +first: U32, +fields: U32, +type_id: U32) -> Result<S.Error,Placed>:
  match body:
    case Placed{Con{child,Nil{}},state}: pushed(state,9,type_id,[key,first,fields,child])
    case _: P.diagnostic(Placed,"image-branch")

def case_node_record(table: Placed, fallback: Placed, +type_id: U32, +slot: U32, +scrutinee: U32, +mode: U32, +rows: U32) -> Result<S.Error,Placed>:
  match table fallback:
    case Placed{words,before} Placed{Con{last,Nil{}},state}:
      pushed(state,8,type_id,Con{slot,Con{scrutinee,Con{mode,Con{rows,List.append(&2,U32,words,Con{last,Nil{}})}}}})
    case _ _: P.diagnostic(Placed,"image-case")

def count_rows_onto(rows: List<&2,P.Row>, +size: U32) -> U32:
  match rows:
    case Nil{}: size
    case Con{head,tail}: count_rows_onto(tail,U32.add(size,1))

def count_rows(rows: List<&2,P.Row>) -> U32:
  count_rows_onto(rows,0)

type Place is Data:
  One{node: P.Node}
  Many{nodes: List<&2,P.Node>}
  More{first: Placed, rest: List<&2,P.Node>}
  Rowset{rows: List<&2,P.Row>, mode: U32, type_id: U32}
  Rowed{row: P.Row, mode: U32, type_id: U32}
  Following{first: Placed, rest: List<&2,P.Row>, mode: U32, type_id: U32}
  Branched{body: Placed, key: U32, first: U32, fields: U32, mode: U32, type_id: U32}
  Fallback{default: Maybe<&2,P.Node>, type_id: U32}
  Finish{table: Placed, default: Maybe<&2,P.Node>, type_id: U32, slot: U32, scrutinee: U32, mode: U32, rows: U32}
  Bodied{value: Placed, body: P.Node, type_id: U32, slot: U32}
  Applied{function: Placed, arguments: List<&2,P.Node>, type_id: U32}

# Children are placed before their parent, left to right. The state that a placed child returns is
# the state its next sibling and its parent continue from, so a step that reads it takes the earlier
# result as a mode, never as a matched call.
def place(fuel: Nat, mode: Place, +state: Nodes) -> Result<S.Error,Placed>:
  match fuel mode:
    case 0n _: P.exhausted(Placed)
    case 1n+ +n One{P.Literal{+type_id,+constant}}: literal_node(constant_index(state,constant),type_id)
    case 1n+ +n One{P.Intrinsic{+type_id,+prim,+operands}}:
      S.bind(Placed,Placed,place(n,Many{operands},state),placed => counted(placed,1,type_id,prim))
    case 1n+ +n One{P.Value{+type_id,+tag}}: pushed(state,3,type_id,Con{tag,Nil{}})
    case 1n+ +n One{P.Construct{+type_id,+tag,+operands}}:
      S.bind(Placed,Placed,place(n,Many{operands},state),placed => counted(placed,4,type_id,tag))
    case 1n+ +n One{P.Reference{+type_id,+slot}}: pushed(state,5,type_id,Con{slot,Nil{}})
    case 1n+ +n One{P.Application{+type_id,+function,+operands}}:
      S.bind(Placed,Placed,place(n,Many{operands},state),placed => counted(placed,6,type_id,function))
    case 1n+ +n One{P.Let{+type_id,+slot,+value,+body}}:
      S.bind(Placed,Placed,place(n,One{value},state),initial => place(n,Bodied{initial,body,type_id,slot},state))
    case 1n+ +n One{P.Case{+type_id,+slot,+scrutinee,+mode,+rows,+default}}:
      S.bind(Placed,Placed,place(n,Rowset{rows,mode,type_id},state),table =>
        place(n,Finish{table,default,type_id,slot,scrutinee,mode,count_rows(rows)},state))
    case 1n+ +n One{P.Closure{+type_id,+live,+slots,+captures,+body}}:
      S.bind(Placed,Placed,place(n,One{body},state),placed => closure_node(placed,type_id,live,slots,captures))
    case 1n+ +n One{P.Invoke{+type_id,+function,+arguments}}:
      S.bind(Placed,Placed,place(n,One{function},state),callee =>
        place(n,Applied{callee,arguments,type_id},state))
    case 1n+ +n One{P.Foreign{+type_id,+foreign,+operands}}:
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
    case 1n+ +n Rowed{P.Missing{},mode,type_id}:
      S.choose(Result<S.Error,Placed>,U32.is_eq(mode,0),u => Done{Placed{Con{P.none(),Nil{}},state}},u => P.diagnostic(Placed,"image-missing-key"))
    case 1n+ +n Rowed{P.Branch{+key,+first,+fields,+body},+mode,+type_id}:
      S.bind(Placed,Placed,place(n,One{body},state),placed => place(n,Branched{placed,key,first,fields,mode,type_id},state))
    case 1n+ +n Branched{Placed{offsets,+later},+key,+first,+fields,+mode,+type_id}:
      S.bind(Placed,Placed,branch_node(Placed{offsets,later},key,first,fields,type_id),branch => row_words(branch,key,mode))
    case 1n+ +n Fallback{None{},type_id}: Done{Placed{Con{P.none(),Nil{}},state}}
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
  Con{U32.add(2,P.count(pack(bytes))),Con{P.count(bytes),pack(bytes)}}

def name_record(text: String) -> List<&2,U32>:
  name_words(utf8(text))

def name_records(names: List<&2,String>, acc: List<&2,List<&2,U32>>) -> List<&2,List<&2,U32>>:
  match names:
    case Nil{}: acc
    case Con{head,tail}: name_records(tail,Con{name_record(head),acc})

def constant_record(constant: P.Constant) -> List<&2,U32>:
  match constant:
    case P.Constant{+kind,+data}: Con{U32.add(3,P.count(data)),Con{kind,Con{P.count(data),data}}}

def constant_records(pool: List<&2,P.Constant>, acc: List<&2,List<&2,U32>>) -> List<&2,List<&2,U32>>:
  match pool:
    case Nil{}: acc
    case Con{head,tail}: constant_records(tail,Con{constant_record(head),acc})

# ---------------------------------------------------------------- sections and header

def bodies(functions: List<&2,P.Function>) -> List<&2,P.Node>:
  match functions:
    case Nil{}: Nil{}
    case Con{P.Function{name,parameters,result,slots,body},tail}: Con{body,bodies(tail)}

def function_limits(parameters: List<&2,U32>, slots: U32) -> Bool:
  Bool.and(U32.is_le(P.count(parameters),4096),U32.is_le(slots,65536))

# [length, name, result, arity, slots, root, parameters...]
def function_record(function: P.Function, +index: U32, +root: U32) -> Result<S.Error,List<&2,U32>>:
  match function:
    case P.Function{name,+parameters,+result,+slots,body}:
      S.choose(Result<S.Error,List<&2,U32>>,function_limits(parameters,slots),u =>
        Done{Con{U32.add(6,P.count(parameters)),Con{index,Con{result,Con{P.count(parameters),Con{slots,Con{root,parameters}}}}}}},u => P.exhausted(List<&2,U32>))

def function_records(functions: List<&2,P.Function>, indices: List<&2,U32>, roots: List<&2,U32>, acc: List<&2,List<&2,U32>>) -> Result<S.Error,List<&2,List<&2,U32>>>:
  match functions indices roots:
    case Nil{} Nil{} Nil{}: Done{List.reverse(&2,List<&2,U32>,acc)}
    case Con{+head,tail} Con{index,more} Con{root,later}:
      S.bind(List<&2,U32>,List<&2,List<&2,U32>>,function_record(head,index,root),record => function_records(tail,more,later,Con{record,acc}))
    case _ _ _: P.diagnostic(List<&2,List<&2,U32>>,"image-functions")

# Section sizes in words: a count word, then each record.
def section_words(records: List<&2,List<&2,U32>>) -> U32:
  U32.add(1,total(records))

type Parts is Data:
  Parts{types: List<&2,List<&2,U32>>, constructors: List<&2,List<&2,U32>>, functions: List<&2,List<&2,U32>>, constants: List<&2,List<&2,U32>>,
        nodes: List<&2,List<&2,U32>>, names: List<&2,List<&2,U32>>, node_count: U32, node_words: U32, entry: U32, main: U32, representation: List<&2,U32>}

def header(total_words: U32, entry: U32, main: U32, o1: U32, o2: U32, o3: U32, o4: U32, o5: U32, o6: U32, representation: List<&2,U32>) -> List<&2,U32>:
  List.append(&2,U32,[P.magic(),1,total_words,entry,main,o1,o2,o3,o4,o5,o6,0],List.append(&2,U32,representation,P.digest()))

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
  Bool.and(U32.is_le(count_records(types,0),P.table_records()),Bool.and(U32.is_le(count_records(constructors,0),P.table_records()),
    Bool.and(U32.is_le(count_records(functions,0),P.table_records()),Bool.and(U32.is_le(count_records(constants,0),P.table_records()),
    Bool.and(U32.is_le(nodes,P.table_records()),U32.is_le(count_records(names,0),P.table_records()))))))

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
    S.choose(Result<S.Error,Encoded>,Bool.and(U32.is_le(total_words,P.image_words()),within_limits(types,constructors,frecords,constants,node_count,named)),u =>
      Done{Encoded{image_records(Parts{types,constructors,frecords,constants,nodes,named,node_count,U32.sub(end,off_nodes),entry,main,representation},
        header(total_words,entry,main,32,o2,o3,o4,off_nodes,o6,representation)),total_words}},u => P.exhausted(Encoded)),u => P.diagnostic(Encoded,"image-layout"))

def name_list(names: Names) -> List<&2,String>:
  match names:
    case Names{list,size}: list

def layout_final(final: Placed, +off_nodes: U32, +types: List<&2,List<&2,U32>>, +constructors: List<&2,List<&2,U32>>, +indices: List<&2,U32>, +names: Names,
    +entry: U32, +representation: List<&2,U32>, +functions: List<&2,P.Function>) -> Result<S.Error,Encoded>:
  match final:
    case Placed{+roots,Nodes{nodes,+end,+pool,pooled,sites,+node_count}}:
      S.bind(List<&2,List<&2,U32>>,Encoded,function_records(functions,indices,roots,Nil{}),frecords =>
        layout_sections(frecords,off_nodes,end,types,constructors,constant_records(pool,Nil{}),nodes,node_count,name_records(name_list(names),Nil{}),entry,P.main_index(functions,0),representation))

# Pass two places the nodes at their final offsets. The constants pool is interned in the same order
# as in the trial pass, so the constants section, which precedes the nodes, has the size it had.
def layout_nodes(fuel: Nat, +off_nodes: U32, +types: List<&2,List<&2,U32>>, +constructors: List<&2,List<&2,U32>>, +indices: List<&2,U32>, +names: Names,
    +entry: U32, +representation: List<&2,U32>, +functions: List<&2,P.Function>) -> Result<S.Error,Encoded>:
  S.bind(Placed,Encoded,place(fuel,Many{bodies(functions)},Nodes{Nil{},U32.add(off_nodes,1),Nil{},0,0,0}),final =>
    layout_final(final,off_nodes,types,constructors,indices,names,entry,representation,functions))

def layout_trial(fuel: Nat, trial: Placed, +types: List<&2,List<&2,U32>>, +constructors: List<&2,List<&2,U32>>, +indices: List<&2,U32>, +names: Names,
    +entry: U32, +representation: List<&2,U32>, +functions: List<&2,P.Function>) -> Result<S.Error,Encoded>:
  match trial:
    case Placed{+roots,Nodes{nodes,end,+pool,pooled,sites,node_count}}:
      S.bind(List<&2,List<&2,U32>>,Encoded,function_records(functions,indices,roots,Nil{}),sized =>
        layout_nodes(fuel,U32.add(32,U32.add(section_words(types),U32.add(section_words(constructors),U32.add(section_words(sized),section_words(constant_records(pool,Nil{})))))),
          types,constructors,indices,names,entry,representation,functions))

def layout_tables(+fuel: Nat, grid: Tables, +entry: U32, +representation: List<&2,U32>, +functions: List<&2,P.Function>) -> Result<S.Error,Encoded>:
  match grid:
    case Tables{Records{+types,tnames,tnext},Records{+constructors,cnames,cnext},Indexed{+indices,+names}}:
      S.bind(Placed,Encoded,place(fuel,Many{bodies(functions)},Nodes{Nil{},0,Nil{},0,0,0}),trial =>
        layout_trial(fuel,trial,types,constructors,indices,names,entry,representation,functions))

# The words of an image: header, then the six sections, as records that the writer streams in order. A name that
# is not an identifier (P.spelled) is refused before any word exists: `decode` would not read it back.
def layout(fuel: Nat, plan: P.Plan) -> Result<S.Error,Encoded>:
  match plan:
    case P.Plan{entry,representation,+shapes,+functions}:
      S.choose(Result<S.Error,Encoded>,P.plan_spelled(shapes,functions),u =>
        layout_tables(fuel,tables(shapes,functions),entry,representation,functions),u => P.unsupported(Encoded,"image-name"))

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

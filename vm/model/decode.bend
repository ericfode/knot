import Base
import ./word.bend as W

# ---------------------------------------------------------------- decoding

def magic() -> U32:
  1196247371

# The pinned base.bend SHA-256, packed little-endian (registry.json).
def digest() -> List<&2,U32>:
  [967372322,1597628945,3931068771,212603004,2186566430,3374278737,2120669052,453228302]


def nth_text(xs: List<&2,String>, +i: U32) -> String:
  match xs:
    case Nil{}: "?"
    case Con{x,rest}: W.choose(String,U32.is_eq(i,0),u => x,u => nth_text(rest,U32.sub(i,1)))

def opcode_name(+op: U32) -> String:
  nth_text(["lit","prim","default","value","con","ref","call","let","case","branch","closure","invoke","foreign"],op)

# Record offsets of one section, in order, and the offset after its last record.
def records(-B: Data, n: Nat, +image: W.Store, +total: U32, +section: U32, +at: U32, found: List<&2,U32>, next: List<&2,U32> -> U32 -> Result<W.Stop,B>) -> Result<W.Stop,B>:
  match n:
    case 0n: next(List.reverse(&2,U32,found),at)
    case 1n+m:
      +size = W.read(image,at)
      W.unless(B,W.or(U32.is_ge(at,total),W.or(U32.is_lt(size,2),U32.is_gt(size,U32.sub(total,at)))),
        String.concat(["section ",U32.show(section)," record length"]),u =>
        records(B,m,image,total,section,U32.add(at,size),Con{at,found},next))

# Six sections, each at its header offset. A count the words after it cannot
# hold, at two words per record, is malformed; one they hold is then bounded
# by SPEC §4's record limit.
def sections(-B: Data, n: Nat, +image: W.Store, +total: U32, +section: U32, +cursor: U32, found: List<&2,List<&2,U32>>, next: List<&2,List<&2,U32>> -> Result<W.Stop,B>) -> Result<W.Stop,B>:
  match n:
    case 0n: W.unless(B,Bool.not(U32.is_eq(cursor,total)),"trailing words",u => next(List.reverse(&2,List<&2,U32>,found)))
    case 1n+m:
      +count = W.read(image,cursor)
      W.unless(B,Bool.not(U32.is_eq(W.read(image,U32.add(5,section)),cursor)),String.concat(["section ",U32.show(section)," offset"]),u =>
      W.unless(B,U32.is_gt(count,U32.div(U32.sub(total,U32.add(cursor,1)),2)),"record count",u =>
      W.limit(B,count,1048576,"records",u =>
      records(B,U32.to_nat(count),image,total,section,U32.add(cursor,1),Nil{},list => end =>
        sections(B,m,image,total,U32.add(section,1),end,Con{list,found},next)))))


def ceil4(+size: U32) -> U32:
  U32.add(U32.div(size,4),Bool.pick(U32,U32.is_eq(U32.mod(size,4),0),0,1))

def valid_utf8(bytes: List<&2,U32>) -> Bool:
  Maybe.is_some(&2,List<&2,U32>,W.scalars(bytes))

def spelled(+bytes: List<&2,U32>, +size: Nat) -> Result<W.Stop,List<&2,U32>>:
  +text = List.take(&2,U32,bytes,size)
  W.unless(List<&2,U32>,W.or(Bool.not(W.zero_all(List.drop(&2,U32,bytes,size))),W.member(text,0)),"name padding",u =>
  W.unless(List<&2,U32>,Bool.not(valid_utf8(text)),"name utf-8",u => Done{text}))

def named(+image: W.Store, +at: U32) -> Result<W.Stop,List<&2,U32>>:
  +size = W.read(image,U32.add(at,1))
  +length = U32.sub(W.read(image,at),1)
  W.unless(List<&2,U32>,W.or(U32.is_eq(size,0),Bool.not(U32.is_eq(length,U32.add(1,ceil4(size))))),"name length",u =>
    spelled(W.unpack(W.slice(U32.to_nat(U32.sub(length,1)),image,U32.add(at,2))),U32.to_nat(size)))

def names(at: List<&2,U32>, +image: W.Store) -> Result<W.Stop,List<&2,List<&2,U32>>>:
  match at:
    case Nil{}: Done{Nil{}}
    case Con{a,rest}:
      W.then(List<&2,U32>,List<&2,List<&2,U32>>,named(image,a),name =>
        W.then(List<&2,List<&2,U32>>,List<&2,List<&2,U32>>,names(rest,image),more => Done{Con{name,more}}))

def listed(xs: List<&2,List<&2,U32>>, +x: List<&2,U32>) -> Bool:
  match xs:
    case Nil{}: False{}
    case Con{y,rest}: W.or(W.same(x,y),listed(rest,x))

def repeated(xs: List<&2,List<&2,U32>>) -> Bool:
  match xs:
    case Nil{}: False{}
    case Con{+x,+rest}: W.or(listed(rest,x),repeated(rest))

def name_at(names: List<&2,List<&2,U32>>, +i: U32) -> Result<W.Stop,List<&2,U32>>:
  match names:
    case Nil{}: Fail{W.Refused{"image","name index"}}
    case Con{+name,+rest}: W.choose(Result<W.Stop,List<&2,U32>>,U32.is_eq(i,0),u => Done{name},u => name_at(rest,U32.sub(i,1)))

def reference(+i: U32, +bound: U32) -> Result<W.Stop,U32>:
  W.choose(Result<W.Stop,U32>,Bool.and(Bool.not(W.is_none(i)),U32.is_ge(i,bound)),u => Fail{W.Refused{"image","type index"}},u => Done{i})

def references(words: List<&2,U32>, +bound: U32) -> Result<W.Stop,List<&2,U32>>:
  match words:
    case Nil{}: Done{Nil{}}
    case Con{w,rest}:
      W.then(U32,List<&2,U32>,reference(w,bound),x =>
        W.then(List<&2,U32>,List<&2,U32>,references(rest,bound),xs => Done{Con{x,xs}}))

# A type row before its constructors are placed: an algebraic row keeps its
# first constructor index and count.
type Row is Data:
  Declared{name: List<&2,U32>, first: U32, count: U32}
  Signature{sort: W.Sort}

def arrow(live: Bool, domain: U32, result: U32) -> W.Sort:
  match live:
    case True{}: W.Arrow{domain,result}
    case False{}: W.Erased{domain,result}

def width(row: Row) -> U32:
  match row:
    case Declared{name,first,count}: count
    case Signature{sort}: 0

def typed(+image: W.Store, +names: List<&2,List<&2,U32>>, +bound: U32, +at: U32, +expect: U32) -> Result<W.Stop,Row>:
  +kind = W.read(image,U32.add(at,1))
  +name = W.read(image,U32.add(at,2))
  +a = W.read(image,U32.add(at,3))
  +b = W.read(image,U32.add(at,4))
  W.unless(Row,W.or(Bool.not(U32.is_eq(W.read(image,at),5)),U32.is_ge(kind,4)),"type record",u =>
    W.choose(Result<W.Stop,Row>,U32.is_eq(kind,0),
      u => W.unless(Row,Bool.not(U32.is_eq(a,expect)),"constructor grouping",u =>
             W.then(List<&2,U32>,Row,name_at(names,name),t => Done{Declared{t,a,b}})),
      u => W.choose(Result<W.Stop,Row>,U32.is_eq(kind,3),
        u => W.unless(Row,W.or(Bool.not(U32.is_eq(a,0)),Bool.not(U32.is_eq(b,0))),"opaque type",u =>
               W.then(List<&2,U32>,Row,name_at(names,name),t => Done{Signature{W.Opaque{t}}})),
        u => W.unless(Row,Bool.not(W.is_none(name)),"arrow name",u =>
               W.then(U32,Row,reference(a,bound),d =>
                 W.then(U32,Row,reference(b,bound),r => Done{Signature{arrow(U32.is_eq(kind,1),d,r)}}))))))

def rows(at: List<&2,U32>, +image: W.Store, +names: List<&2,List<&2,U32>>, +bound: U32, +expect: U32) -> Result<W.Stop,List<&2,Row>>:
  match at:
    case Nil{}: Done{Nil{}}
    case Con{a,rest}:
      W.then(Row,List<&2,Row>,typed(image,names,bound,a,expect),+row =>
        W.then(List<&2,Row>,List<&2,Row>,rows(rest,image,names,bound,U32.add(expect,width(row))),more => Done{Con{row,more}}))

def widths(rows: List<&2,Row>) -> U32:
  match rows:
    case Nil{}: 0
    case Con{row,rest}: U32.add(width(row),widths(rest))

def slot_of(row: Row, +tag: U32) -> U32:
  match row:
    case Declared{name,+first,+count}: W.choose(U32,U32.is_lt(tag,count),u => U32.add(first,tag),u => W.none())
    case Signature{sort}: W.none()

# The global constructor position of `tag` in type row `t`, or none.
def position(rows: List<&2,Row>, +t: U32, +tag: U32) -> U32:
  match rows:
    case Nil{}: W.none()
    case Con{row,rest}: W.choose(U32,U32.is_eq(t,0),u => slot_of(row,tag),u => position(rest,U32.sub(t,1),tag))

# Constructor records fill their row positions; `filled` maps a position to
# its record offset plus one.
def placed(at: List<&2,U32>, +image: W.Store, +names: List<&2,List<&2,U32>>, +rows: List<&2,Row>, +bound: U32, +filled: W.Store) -> Result<W.Stop,W.Store>:
  match at:
    case Nil{}: Done{filled}
    case Con{+a,rest}:
      +length = U32.sub(W.read(image,a),1)
      +place = position(rows,W.read(image,U32.add(a,1)),W.read(image,U32.add(a,2)))
      W.unless(W.Store,W.or(U32.is_lt(length,4),W.or(Bool.not(U32.is_eq(length,U32.add(4,W.read(image,U32.add(a,4))))),U32.is_ge(W.read(image,U32.add(a,1)),bound))),"constructor record",u =>
      W.unless(W.Store,W.or(W.is_none(place),Bool.not(U32.is_eq(W.read(filled,place),0))),"constructor tag",u =>
      W.then(List<&2,U32>,W.Store,name_at(names,W.read(image,U32.add(a,3))),t =>
      W.then(List<&2,U32>,W.Store,references(W.slice(U32.to_nat(W.read(image,U32.add(a,4))),image,U32.add(a,5)),bound),fields =>
        placed(rest,image,names,rows,bound,W.write(filled,place,U32.add(a,1)))))))

def constructor(+image: W.Store, +names: List<&2,List<&2,U32>>, +at: U32) -> W.Constructor:
  W.Constructor{Result.default(&1,&1,W.Stop,List<&2,U32>,name_at(names,W.read(image,U32.add(at,3))),Nil{}),W.slice(U32.to_nat(W.read(image,U32.add(at,4))),image,U32.add(at,5))}

def constructors(n: Nat, +image: W.Store, +names: List<&2,List<&2,U32>>, +filled: W.Store, +place: U32) -> List<&2,W.Constructor>:
  match n:
    case 0n: Nil{}
    case 1n+m: Con{constructor(image,names,U32.sub(W.read(filled,place),1)),constructors(m,image,names,filled,U32.add(place,1))}

def sorted_row(row: Row, +image: W.Store, +names: List<&2,List<&2,U32>>, +filled: W.Store) -> W.Sort:
  match row:
    case Declared{name,+first,+count}: W.Algebraic{name,constructors(U32.to_nat(count),image,names,filled,first)}
    case Signature{sort}: sort

def sorts(rows: List<&2,Row>, +image: W.Store, +names: List<&2,List<&2,U32>>, +filled: W.Store) -> List<&2,W.Sort>:
  match rows:
    case Nil{}: Nil{}
    case Con{row,rest}: Con{sorted_row(row,image,names,filled),sorts(rest,image,names,filled)}

def constants(at: List<&2,U32>, +image: W.Store) -> Result<W.Stop,List<&2,W.Constant>>:
  match at:
    case Nil{}: Done{Nil{}}
    case Con{+a,rest}:
      +length = U32.sub(W.read(image,a),1)
      +kind = W.read(image,U32.add(a,1))
      +n = W.read(image,U32.add(a,2))
      W.unless(List<&2,W.Constant>,W.or(U32.is_lt(length,2),W.or(U32.is_ge(kind,4),Bool.not(U32.is_eq(length,U32.add(2,n))))),"constant record",u =>
      W.unless(List<&2,W.Constant>,Bool.and(Bool.not(U32.is_eq(kind,3)),Bool.not(U32.is_eq(n,1))),"scalar constant width",u =>
      W.then(List<&2,W.Constant>,List<&2,W.Constant>,constants(rest,image),more =>
        Done{Con{W.Constant{kind,W.slice(U32.to_nat(n),image,U32.add(a,3))},more}})))

# Record lengths of SPEC §3: fixed forms, variadic forms, Case and Closure.
def misshaped(+op: U32, +x: U32, +image: W.Store, +at: U32) -> Bool:
  +x1 = W.read(image,U32.add(at,4))
  +x2 = W.read(image,U32.add(at,5))
  +x3 = W.read(image,U32.add(at,6))
  W.choose(Bool,W.or(W.or(U32.is_eq(op,0),U32.is_eq(op,3)),W.or(U32.is_eq(op,5),U32.is_eq(op,2))),u => Bool.not(U32.is_eq(x,1)),u =>
  W.choose(Bool,U32.is_eq(op,7),u => Bool.not(U32.is_eq(x,3)),u =>
  W.choose(Bool,U32.is_eq(op,9),u => Bool.not(U32.is_eq(x,4)),u =>
  W.choose(Bool,U32.is_eq(op,8),u =>
    W.or(U32.is_lt(x,4),W.or(U32.is_ge(x2,2),W.or(U32.is_gt(x3,x),
      Bool.not(U32.is_eq(x,U32.add(5,U32.mul(x3,Bool.pick(U32,U32.is_eq(x2,0),1,2)))))))),u =>
  W.choose(Bool,U32.is_eq(op,10),u => W.or(U32.is_lt(x,5),Bool.not(U32.is_eq(x,U32.add(5,x3)))),u =>
    W.or(U32.is_lt(x,2),Bool.not(U32.is_eq(x,U32.add(2,x1)))))))))

# A Closure's `slots` sizes its Activation as a function's does; no other
# node has one.
def closure_slots(+op: U32, +image: W.Store, +at: U32) -> U32:
  W.choose(U32,U32.is_eq(op,10),u => W.read(image,U32.add(at,5)),u => 0)

def shaped(at: List<&2,U32>, +image: W.Store, starts: W.Store) -> Result<W.Stop,W.Store>:
  match at:
    case Nil{}: Done{starts}
    case Con{+a,rest}:
      +length = U32.sub(W.read(image,a),1)
      +op = W.read(image,U32.add(a,1))
      W.unless(W.Store,W.or(U32.is_lt(length,2),U32.is_ge(op,13)),"node record",u =>
      W.unless(W.Store,misshaped(op,U32.sub(length,2),image,a),String.append(opcode_name(op)," length"),u =>
      W.limit(W.Store,closure_slots(op,image,a),65536,"slots",u =>
        shaped(rest,image,W.write(starts,a,1)))))

# How a child record may be used: an operand, a tag-table row, a key-table row
# with its key, or a Case default.
type Role is Data:
  Operand{}
  Tagged{}
  Keyed{key: U32}
  Fallback{}

type Job is Data:
  Job{offset: U32, role: Role}

# Owner marks: bit 0 for a child, bit 1 for a function root.
type Claims is Data:
  Claims{marks: W.Store, owned: U32, roots: U32}

type Env is Data:
  Env{image: W.Store, starts: W.Store, types: U32, constants: List<&2,W.Constant>}

def image_of(env: Env) -> W.Store:
  match env:
    case Env{image,starts,types,constants}: image

def types_of(env: Env) -> U32:
  match env:
    case Env{image,starts,types,constants}: types

def claim(+env: Env, +parent: U32, +at: U32, +claims: Claims) -> Result<W.Stop,Claims>:
  match env claims:
    case Env{image,+starts,types,constants} Claims{+marks,+owned,+roots}:
      W.choose(Result<W.Stop,Claims>,W.is_none(parent),u => Done{Claims{marks,owned,roots}},u =>
      W.unless(Claims,U32.is_eq(W.read(starts,at),0),"child offset",u =>
      W.unless(Claims,U32.is_ge(at,parent),"child after parent",u =>
      W.unless(Claims,U32.is_eq(U32.and(W.read(marks,at),1),1),"shared node",u =>
        Done{Claims{W.write(marks,at,U32.add(W.read(marks,at),1)),U32.add(owned,1),roots}}))))

def rooted(+env: Env, +at: U32, +claims: Claims) -> Result<W.Stop,Claims>:
  match env claims:
    case Env{image,+starts,types,constants} Claims{+marks,+owned,+roots}:
      W.unless(Claims,W.or(U32.is_eq(W.read(starts,at),0),Bool.not(U32.is_eq(W.read(marks,at),0))),"function root",u =>
        Done{Claims{W.write(marks,at,2),owned,U32.add(roots,1)}})

def is_arm(+op: U32) -> Bool:
  W.or(U32.is_eq(op,2),U32.is_eq(op,9))

def is_operand(role: Role) -> Bool:
  match role:
    case Operand{}: True{}
    case _: False{}

def inspected(+env: Env, +at: U32, role: Role) -> Result<W.Stop,Unit>:
  match env:
    case Env{+image,starts,+types,+constants}:
      +t = W.read(image,U32.add(at,2))
      +op = W.read(image,U32.add(at,1))
      W.unless(Unit,Bool.and(Bool.not(W.is_none(t)),U32.is_ge(t,types)),"type index",u =>
      W.unless(Unit,Bool.and(is_arm(op),is_operand(role)),"standalone arm",u =>
      W.unless(Unit,Bool.and(U32.is_eq(op,0),U32.is_ge(W.read(image,U32.add(at,3)),W.count(W.Constant,constants))),"constant index",u =>
        Done{Unit{}})))

def operands(words: List<&2,U32>) -> List<&2,Job>:
  match words:
    case Nil{}: Nil{}
    case Con{w,rest}: Con{Job{w,Operand{}},operands(rest)}

def tag_rows(words: List<&2,U32>) -> List<&2,Job>:
  match words:
    case Nil{}: Nil{}
    case Con{+w,+rest}: W.choose(List<&2,Job>,W.is_none(w),u => tag_rows(rest),u => Con{Job{w,Tagged{}},tag_rows(rest)})

def key_rows(n: Nat, +image: W.Store, +at: U32) -> List<&2,Job>:
  match n:
    case 0n: Nil{}
    case 1n+m: Con{Job{W.read(image,U32.add(at,1)),Keyed{W.read(image,at)}},key_rows(m,image,U32.add(at,2))}

def fallback(+w: U32) -> List<&2,Job>:
  W.choose(List<&2,Job>,W.is_none(w),u => Nil{},u => [Job{w,Fallback{}}])

def operand_jobs(+image: W.Store, +x: U32) -> List<&2,Job>:
  operands(W.slice(U32.to_nat(W.read(image,U32.add(x,1))),image,U32.add(x,2)))

# Children in SPEC §3 order; an absent row or default has no record.
def children(op: Nat, +image: W.Store, +x: U32, +last: U32) -> List<&2,Job>:
  match op:
    case 1n: operand_jobs(image,x)
    case 2n: operands([W.read(image,x)])
    case 4n: operand_jobs(image,x)
    case 6n: operand_jobs(image,x)
    case 7n: operands([W.read(image,U32.add(x,1)),W.read(image,U32.add(x,2))])
    case 8n:
      +n = W.read(image,U32.add(x,3))
      List.append(&2,Job,W.choose(List<&2,Job>,U32.is_eq(W.read(image,U32.add(x,2)),0),
        u => tag_rows(W.slice(U32.to_nat(n),image,U32.add(x,4))),
        u => key_rows(U32.to_nat(n),image,U32.add(x,4))),fallback(last))
    case 9n: operands([W.read(image,U32.add(x,3))])
    case 10n: operands([last])
    case 11n: Con{Job{W.read(image,x),Operand{}},operand_jobs(image,x)}
    case 12n: operand_jobs(image,x)
    case _: Nil{}

def kids(+image: W.Store, +at: U32) -> List<&2,Job>:
  children(U32.to_nat(W.read(image,U32.add(at,1))),image,U32.add(at,3),W.read(image,U32.sub(U32.add(at,W.read(image,at)),1)))

def blank() -> W.Node:
  W.Value{W.none(),W.none()}

def first(nodes: List<&2,W.Node>) -> W.Node:
  match nodes:
    case Nil{}: blank()
    case Con{node,rest}: node

def second(nodes: List<&2,W.Node>) -> W.Node:
  match nodes:
    case Con{a,Con{b,rest}}: b
    case _: blank()

def rest_of(nodes: List<&2,W.Node>) -> List<&2,W.Node>:
  match nodes:
    case Nil{}: Nil{}
    case Con{node,rest}: rest

def final(nodes: List<&2,W.Node>) -> W.Node:
  match nodes:
    case Nil{}: blank()
    case Con{node,Nil{}}: node
    case Con{node,rest}: final(rest)

def constant_at(constants: List<&2,W.Constant>, +i: U32) -> W.Constant:
  match constants:
    case Nil{}: W.Constant{W.none(),Nil{}}
    case Con{+c,+rest}: W.choose(W.Constant,U32.is_eq(i,0),u => c,u => constant_at(rest,U32.sub(i,1)))

def filled_rows(words: List<&2,U32>, nodes: List<&2,W.Node>) -> List<&2,Maybe<&2,W.Node>>:
  match words nodes:
    case Nil{} _: Nil{}
    case Con{+w,+rest} Con{+node,+more}:
      W.choose(List<&2,Maybe<&2,W.Node>>,W.is_none(w),u => Con{None{},filled_rows(rest,Con{node,more})},u => Con{Some{node},filled_rows(rest,more)})
    case Con{w,rest} Nil{}: Con{None{},filled_rows(rest,Nil{})}

def keyed_rows(n: Nat, nodes: List<&2,W.Node>) -> List<&2,Maybe<&2,W.Node>>:
  match n nodes:
    case 1n+m Con{node,more}: Con{Some{node},keyed_rows(m,more)}
    case _ _: Nil{}

def is_branch(node: W.Node) -> Bool:
  match node:
    case W.Branch{key,first,fields,body}: True{}
    case _: False{}

def is_default(node: W.Node) -> Bool:
  match node:
    case W.Default{body}: True{}
    case _: False{}

def rows_are_branches(rows: List<&2,Maybe<&2,W.Node>>) -> Bool:
  match rows:
    case Nil{}: True{}
    case Con{None{},rest}: rows_are_branches(rest)
    case Con{Some{node},rest}: Bool.and(is_branch(node),rows_are_branches(rest))

def default_is_default(fallback: Maybe<&2,W.Node>) -> Bool:
  match fallback:
    case None{}: True{}
    case Some{node}: is_default(node)

def cased(+image: W.Store, +at: U32, +types: U32, +nodes: List<&2,W.Node>) -> Result<W.Stop,W.Node>:
  +x = U32.add(at,3)
  +mode = W.read(image,U32.add(x,2))
  +n = W.read(image,U32.add(x,3))
  +rows = W.choose(List<&2,Maybe<&2,W.Node>>,U32.is_eq(mode,0),u => filled_rows(W.slice(U32.to_nat(n),image,U32.add(x,4)),nodes),u => keyed_rows(U32.to_nat(n),nodes))
  +fallback = W.choose(Maybe<&2,W.Node>,W.is_none(W.read(image,U32.sub(U32.add(at,W.read(image,at)),1))),u => None{},u => Some{final(nodes)})
  W.unless(W.Node,Bool.not(Bool.and(rows_are_branches(rows),default_is_default(fallback))),"case arm kind",u =>
    W.then(U32,W.Node,reference(W.read(image,U32.add(x,1)),types),s => Done{W.Case{W.read(image,U32.add(at,2)),W.read(image,x),s,mode,rows,fallback}}))

def keyed(role: Role, node: W.Node) -> Result<W.Stop,W.Node>:
  match role node:
    case Keyed{+k} W.Branch{+key,first,fields,body}:
      W.choose(Result<W.Stop,W.Node>,U32.is_eq(key,k),u => Done{W.Branch{key,first,fields,body}},u => Fail{W.Refused{"image","case key"}})
    case Keyed{k} _: Fail{W.Refused{"image","case key"}}
    case _ _: Done{node}

def built(op: Nat, +image: W.Store, +types: U32, +constants: List<&2,W.Constant>, +at: U32, +t: U32, +x0: U32, +x1: U32, +x2: U32, +nodes: List<&2,W.Node>) -> Result<W.Stop,W.Node>:
  match op:
    case 0n: Done{W.Literal{t,constant_at(constants,x0)}}
    case 1n: Done{W.Intrinsic{t,x0,nodes}}
    case 2n: Done{W.Default{first(nodes)}}
    case 3n: Done{W.Value{t,x0}}
    case 4n: Done{W.Construct{t,x0,nodes}}
    case 5n: Done{W.Reference{t,x0}}
    case 6n: Done{W.Application{t,x0,nodes}}
    case 7n: Done{W.Let{t,x0,first(nodes),second(nodes)}}
    case 8n: cased(image,at,types,nodes)
    case 9n: Done{W.Branch{x0,x1,x2,first(nodes)}}
    case 10n: Done{W.Closure{t,x1,x2,W.slice(U32.to_nat(W.read(image,U32.add(at,6))),image,U32.add(at,7)),first(nodes)}}
    case 11n: Done{W.Invoke{t,first(nodes),rest_of(nodes)}}
    case 12n: Done{W.Foreign{t,x0,nodes}}
    case _: Fail{W.Refused{"image","opcode"}}

def assembled(+env: Env, +at: U32, nodes: List<&2,W.Node>) -> Result<W.Stop,W.Node>:
  match env:
    case Env{+image,starts,+types,+constants}:
      built(U32.to_nat(W.read(image,U32.add(at,1))),image,types,constants,at,W.read(image,U32.add(at,2)),
        W.read(image,U32.add(at,3)),W.read(image,U32.add(at,4)),W.read(image,U32.add(at,5)),nodes)

# Post-order trees, each child claimed once and before its parent. Fuel bounds
# the nesting of pending jobs by the image's word count.
def forest(fuel: Nat, +env: Env, +parent: U32, work: List<&2,Job>, claims: Claims, done: List<&2,W.Node>, next: List<&2,W.Node> -> Claims -> Result<W.Stop,W.Plan>) -> Result<W.Stop,W.Plan>:
  match fuel work:
    case _ Nil{}: next(List.reverse(&2,W.Node,done),claims)
    case 0n _: Fail{W.Refused{"image","node depth"}}
    case 1n+ +f Con{Job{+at,+role},rest}:
      W.then(Claims,W.Plan,claim(env,parent,at,claims),claims =>
      W.then(Unit,W.Plan,inspected(env,at,role),u =>
      forest(f,env,at,kids(image_of(env),at),claims,Nil{},nodes => claims =>
      W.then(W.Node,W.Plan,assembled(env,at,nodes),node =>
      W.then(W.Node,W.Plan,keyed(role,node),node =>
      forest(f,env,parent,rest,claims,Con{node,done},next))))))

def functions(at: List<&2,U32>, +fuel: Nat, +env: Env, +names: List<&2,List<&2,U32>>, claims: Claims, found: List<&2,W.Function>, next: List<&2,W.Function> -> Claims -> Result<W.Stop,W.Plan>) -> Result<W.Stop,W.Plan>:
  match at:
    case Nil{}: next(List.reverse(&2,W.Function,found),claims)
    case Con{+a,rest}:
      +image = image_of(env)
      +length = U32.sub(W.read(image,a),1)
      +arity = W.read(image,U32.add(a,3))
      +root = W.read(image,U32.add(a,5))
      W.unless(W.Plan,W.or(U32.is_lt(length,5),Bool.not(U32.is_eq(length,U32.add(5,arity)))),"function record",u =>
      W.limit(W.Plan,arity,4096,"arity",u =>
      W.limit(W.Plan,W.read(image,U32.add(a,4)),65536,"slots",u =>
      W.then(Claims,W.Plan,rooted(env,root,claims),claims =>
      W.then(List<&2,U32>,W.Plan,name_at(names,W.read(image,U32.add(a,1))),name =>
      W.then(List<&2,U32>,W.Plan,references(W.slice(U32.to_nat(arity),image,U32.add(a,6)),types_of(env)),parameters =>
      W.then(U32,W.Plan,reference(W.read(image,U32.add(a,2)),types_of(env)),result =>
      forest(fuel,env,W.none(),[Job{root,Operand{}}],claims,Nil{},nodes => claims =>
        functions(rest,fuel,env,names,claims,Con{W.Function{name,parameters,result,W.read(image,U32.add(a,4)),first(nodes)},found},next)))))))))

def name_of(f: W.Function) -> List<&2,U32>:
  match f:
    case W.Function{name,parameters,result,slots,body}: name

def main_bytes() -> List<&2,U32>:
  [109,97,105,110]

def function_at(functions: List<&2,W.Function>, +i: U32) -> Maybe<&2,W.Function>:
  match functions:
    case Nil{}: None{}
    case Con{+f,+rest}: W.choose(Maybe<&2,W.Function>,U32.is_eq(i,0),u => Some{f},u => function_at(rest,U32.sub(i,1)))

def names_main(found: Maybe<&2,W.Function>) -> Bool:
  match found:
    case None{}: False{}
    case Some{f}: W.same(name_of(f),main_bytes())

def planned(+image: W.Store, +nodes: U32, +sorts: List<&2,W.Sort>, +functions: List<&2,W.Function>, claims: Claims) -> Result<W.Stop,W.Plan>:
  match claims:
    case Claims{marks,owned,roots}:
      +main = W.read(image,4)
      W.unless(W.Plan,Bool.not(U32.is_eq(U32.add(owned,roots),nodes)),"unreachable node",u =>
      W.unless(W.Plan,Bool.and(Bool.not(W.is_none(main)),Bool.not(names_main(function_at(functions,main)))),"main index",u =>
      W.then(List<&2,U32>,W.Plan,references(W.slice(12n,image,12),W.count(W.Sort,sorts)),representation =>
        Done{W.Plan{W.read(image,3),sorts,functions,representation}})))

def decoded(lists: List<&2,List<&2,U32>>, +image: W.Store, +total: U32) -> Result<W.Stop,W.Plan>:
  match lists:
    case Con{+t,Con{+c,Con{f,Con{k,Con{+n,Con{m,Nil{}}}}}}}:
      W.then(List<&2,List<&2,U32>>,W.Plan,names(m,image),+names =>
      W.unless(W.Plan,repeated(names),"duplicate name",u =>
      W.then(List<&2,Row>,W.Plan,rows(t,image,names,W.count(U32,t),0),+rows =>
      W.unless(W.Plan,Bool.not(U32.is_eq(widths(rows),W.count(U32,c))),"constructor count",u =>
      W.then(W.Store,W.Plan,placed(c,image,names,rows,W.count(U32,t),W.empty()),+filled =>
      W.then(List<&2,W.Constant>,W.Plan,constants(k,image),+constants =>
      W.then(W.Store,W.Plan,shaped(n,image,W.empty()),+starts =>
      functions(f,U32.to_nat(total),Env{image,starts,W.count(U32,t),constants},names,Claims{W.empty(),0,0},Nil{},found => claims =>
        planned(image,W.count(U32,n),sorts(rows,image,names,filled),found,claims)))))))))
    case _: Fail{W.Refused{"image","sections"}}

# Header, sections and records of SPEC §2, refused in serializer.decode's order.
def decode(+words: List<&2,U32>) -> Result<W.Stop,W.Plan>:
  +total = W.count(U32,words)
  +image = W.stored(words,W.empty(),0)
  W.unless(W.Plan,W.or(Bool.not(U32.is_eq(W.read(image,0),magic())),Bool.not(U32.is_eq(W.read(image,1),1))),"magic",u =>
  W.unless(W.Plan,Bool.not(U32.is_eq(W.read(image,2),total)),"total",u =>
  W.unless(W.Plan,W.or(U32.is_ge(W.read(image,3),2),Bool.not(U32.is_eq(W.read(image,11),0))),"header",u =>
  W.unless(W.Plan,Bool.not(W.same(W.slice(8n,image,24),digest())),"registry digest",u =>
    sections(W.Plan,6n,image,total,0,32,Nil{},lists => decoded(lists,image,total))))))

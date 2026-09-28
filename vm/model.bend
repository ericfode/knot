import Base

# The normative model of knot-image-1 and knot-vm-1 (vm/SPEC.md): the image is
# a read-only word store, the heap a word store at SPEC byte addresses, and
# each machine transition a function of those stores and a few registers.
# Words are u32; `none` is 0xffffffff. A refusal reason is SPEC §4's, spelled
# as vm/serializer.py spells its first problem.

def none() -> U32:
  4294967295

def choose(-A: Type, condition: Bool, yes: Unit -> A, no: Unit -> A) -> A:
  match condition:
    case True{}: yes(Unit{})
    case False{}: no(Unit{})

def then(-A: Data, -B: Data, result: Result<String,A>, next: A -> Result<String,B>) -> Result<String,B>:
  match result:
    case Fail{reason}: Fail{reason}
    case Done{value}: next(value)

def unless(-A: Data, bad: Bool, reason: String, next: Unit -> Result<String,A>) -> Result<String,A>:
  choose(Result<String,A>,bad,u => Fail{reason},next)

def is_none(+w: U32) -> Bool:
  U32.is_eq(w,none())

# ---------------------------------------------------------------- word store

# A trie over key bits, most significant first. Absent keys read 0.
type Trie is Data:
  Void{}
  Leaf{word: U32}
  Fork{low: Trie, high: Trie}

# Keys below 2^depth fit; writing a larger key deepens the root.
type Store is Data:
  Store{depth: Nat, root: Trie}

def bit(+key: U32, level: Nat) -> Bool:
  U32.is_eq(U32.and(U32.shrn(key,level),1),1)

def side(high: Bool, low: Trie, up: Trie) -> Trie:
  match high:
    case False{}: low
    case True{}: up

def pair(high: Bool, near: Trie, far: Trie) -> Trie:
  match high:
    case False{}: Fork{near,far}
    case True{}: Fork{far,near}

def seek(level: Nat, trie: Trie, +key: U32) -> U32:
  match level trie:
    case 0n Leaf{word}: word
    case 1n+ +l Fork{low,high}: seek(l,side(bit(key,l),low,high),key)
    case _ _: 0

def plant(level: Nat, trie: Trie, +key: U32, word: U32) -> Trie:
  match level trie:
    case 0n _: Leaf{word}
    case 1n+ +l Fork{+low,+high}:
      +up = bit(key,l)
      pair(up,plant(l,side(up,low,high),key,word),side(Bool.not(up),low,high))
    case 1n+ +l _: pair(bit(key,l),plant(l,Void{},key,word),Void{})

def inside(+key: U32, +depth: Nat) -> Bool:
  Bool.or(Nat.is_ge(depth,32n),U32.is_eq(U32.shrn(key,depth),0))

def read(store: Store, +key: U32) -> U32:
  match store:
    case Store{+depth,root}: choose(U32,inside(key,depth),u => seek(depth,root,key),u => 0)

def deepen(fuel: Nat, +depth: Nat, +root: Trie, +key: U32) -> Store:
  match fuel:
    case 0n: Store{depth,root}
    case 1n+n:
      choose(Store,inside(key,depth),u => Store{depth,root},u => deepen(n,1n+depth,Fork{root,Void{}},key))

def grown(store: Store, +key: U32) -> Store:
  match store:
    case Store{depth,root}: deepen(32n,depth,root,key)

def planted(store: Store, +key: U32, word: U32) -> Store:
  match store:
    case Store{+depth,root}: Store{depth,plant(depth,root,key,word)}

def write(store: Store, +key: U32, word: U32) -> Store:
  planted(grown(store,key),key,word)

def empty() -> Store:
  Store{0n,Void{}}

def stored(words: List<&2,U32>, store: Store, +key: U32) -> Store:
  match words:
    case Nil{}: store
    case Con{word,rest}: stored(rest,write(store,key,word),U32.add(key,1))

# ---------------------------------------------------------------- bytes and words

# Four bytes make one little-endian word; a short tail makes none.
def pack(bytes: List<&2,U32>) -> List<&2,U32>:
  match bytes:
    case Con{a,Con{b,Con{c,Con{d,rest}}}}:
      Con{U32.add(U32.add(a,U32.shln(b,8n)),U32.add(U32.shln(c,16n),U32.shln(d,24n))),pack(rest)}
    case _: Nil{}

def unpack(words: List<&2,U32>) -> List<&2,U32>:
  match words:
    case Nil{}: Nil{}
    case Con{+w,rest}:
      Con{U32.and(w,255),Con{U32.and(U32.shrn(w,8n),255),Con{U32.and(U32.shrn(w,16n),255),Con{U32.shrn(w,24n),unpack(rest)}}}}

def count(-A: Data, xs: List<&2,A>) -> U32:
  match xs:
    case Nil{}: 0
    case Con{x,rest}: U32.add(count(A,rest),1)

def same(xs: List<&2,U32>, ys: List<&2,U32>) -> Bool:
  match xs ys:
    case Nil{} Nil{}: True{}
    case Con{x,xt} Con{y,yt}: Bool.and(U32.is_eq(x,y),same(xt,yt))
    case _ _: False{}

def nth(xs: List<&2,U32>, +i: U32) -> U32:
  match xs:
    case Nil{}: none()
    case Con{x,rest}: choose(U32,U32.is_eq(i,0),u => x,u => nth(rest,U32.sub(i,1)))

def member(xs: List<&2,U32>, +x: U32) -> Bool:
  match xs:
    case Nil{}: False{}
    case Con{y,rest}: Bool.or(U32.is_eq(x,y),member(rest,x))

def range(n: Nat, +from: U32) -> List<&2,U32>:
  match n:
    case 0n: Nil{}
    case 1n+m: Con{from,range(m,U32.add(from,1))}

# ---------------------------------------------------------------- UTF-8

# A decoder state: continuation bytes still needed, the admitted range of the
# next byte, the payload bits so far, and the scalars already decoded.
type Utf8 is Data:
  Utf8{need: U32, low: U32, high: U32, code: U32, codes: List<&2,U32>}

def within(+b: U32, +low: U32, +high: U32) -> Bool:
  Bool.and(U32.is_ge(b,low),U32.is_le(b,high))

def settle(state: Utf8) -> Utf8:
  match state:
    case Utf8{+need,+low,+high,+code,+codes}:
      choose(Utf8,U32.is_eq(need,0),u => Utf8{0,128,191,0,Con{code,codes}},u => Utf8{need,low,high,code,codes})

# The lead byte fixes the continuation count, the next byte's range and its bits.
def lead(+b: U32, +codes: List<&2,U32>) -> Maybe<&2,Utf8>:
  choose(Maybe<&2,Utf8>,U32.is_lt(b,128),u => Some{settle(Utf8{0,128,191,b,codes})},u =>
  choose(Maybe<&2,Utf8>,within(b,194,223),u => Some{Utf8{1,128,191,U32.and(b,31),codes}},u =>
  choose(Maybe<&2,Utf8>,U32.is_eq(b,224),u => Some{Utf8{2,160,191,0,codes}},u =>
  choose(Maybe<&2,Utf8>,U32.is_eq(b,237),u => Some{Utf8{2,128,159,13,codes}},u =>
  choose(Maybe<&2,Utf8>,within(b,225,239),u => Some{Utf8{2,128,191,U32.and(b,15),codes}},u =>
  choose(Maybe<&2,Utf8>,U32.is_eq(b,240),u => Some{Utf8{3,144,191,0,codes}},u =>
  choose(Maybe<&2,Utf8>,U32.is_eq(b,244),u => Some{Utf8{3,128,143,4,codes}},u =>
  choose(Maybe<&2,Utf8>,within(b,241,243),u => Some{Utf8{3,128,191,U32.and(b,7),codes}},u => None{}))))))))

def advance(state: Utf8, +b: U32) -> Maybe<&2,Utf8>:
  match state:
    case Utf8{+need,+low,+high,+code,+codes}:
      choose(Maybe<&2,Utf8>,U32.is_eq(need,0),u => lead(b,codes),u =>
        choose(Maybe<&2,Utf8>,within(b,low,high),
          u => Some{settle(Utf8{U32.sub(need,1),128,191,U32.add(U32.shln(code,6n),U32.and(b,63)),codes})},
          u => None{}))

def finished(state: Utf8) -> Maybe<&2,List<&2,U32>>:
  match state:
    case Utf8{+need,low,high,code,+codes}:
      choose(Maybe<&2,List<&2,U32>>,U32.is_eq(need,0),u => Some{List.reverse(&2,U32,codes)},u => None{})

# Strict UTF-8 to scalars: no overlongs, surrogates or codes above U+10FFFF.
def utf8(bytes: List<&2,U32>, state: Maybe<&2,Utf8>) -> Maybe<&2,List<&2,U32>>:
  match bytes state:
    case _ None{}: None{}
    case Nil{} Some{s}: finished(s)
    case Con{b,rest} Some{s}: utf8(rest,advance(s,b))

def scalars(bytes: List<&2,U32>) -> Maybe<&2,List<&2,U32>>:
  utf8(bytes,Some{Utf8{0,128,191,0,Nil{}}})

# ---------------------------------------------------------------- the plan

# An image decodes to its plan: the tables and post-order node trees without
# offsets, interned names or constant indices. Re-encoding a plan is canonical.
type Constructor is Data:
  Constructor{name: List<&2,U32>, fields: List<&2,U32>}

type Sort is Data:
  Algebraic{name: List<&2,U32>, constructors: List<&2,Constructor>}
  Arrow{domain: U32, result: U32}
  Erased{domain: U32, result: U32}
  Opaque{name: List<&2,U32>}

type Constant is Data:
  Constant{kind: U32, data: List<&2,U32>}

type Node is Data:
  Literal{result: U32, constant: Constant}
  Intrinsic{result: U32, prim: U32, operands: List<&2,Node>}
  Default{body: Node}
  Value{result: U32, tag: U32}
  Construct{result: U32, tag: U32, operands: List<&2,Node>}
  Reference{result: U32, slot: U32}
  Application{result: U32, function: U32, operands: List<&2,Node>}
  Let{result: U32, slot: U32, value: Node, body: Node}
  Case{result: U32, slot: U32, scrutinee: U32, mode: U32, rows: List<&2,Maybe<&2,Node>>, otherwise: Maybe<&2,Node>}
  Branch{key: U32, first: U32, fields: U32, body: Node}
  Closure{result: U32, live: U32, slots: U32, captures: List<&2,U32>, body: Node}
  Invoke{result: U32, function: Node, arguments: List<&2,Node>}
  Foreign{result: U32, foreign: U32, operands: List<&2,Node>}

type Function is Data:
  Function{name: List<&2,U32>, parameters: List<&2,U32>, result: U32, slots: U32, body: Node}

# `representation` holds header words 12-23: Nat, U32, Char, String, Bool, Cmp,
# Unit, List, Result, Sigma, IO.OP and File, each a type index or none.
type Plan is Data:
  Plan{entry: U32, types: List<&2,Sort>, functions: List<&2,Function>, representation: List<&2,U32>}

# ---------------------------------------------------------------- decoding

def magic() -> U32:
  1196247371

# The pinned base.bend SHA-256, packed little-endian (registry.json).
def digest() -> List<&2,U32>:
  [967372322,1597628945,3931068771,212603004,2186566430,3374278737,2120669052,453228302]

def slice(n: Nat, +image: Store, +from: U32) -> List<&2,U32>:
  match n:
    case 0n: Nil{}
    case 1n+m: Con{read(image,from),slice(m,image,U32.add(from,1))}

def nth_text(xs: List<&2,String>, +i: U32) -> String:
  match xs:
    case Nil{}: "?"
    case Con{x,rest}: choose(String,U32.is_eq(i,0),u => x,u => nth_text(rest,U32.sub(i,1)))

def opcode_name(+op: U32) -> String:
  nth_text(["lit","prim","default","value","con","ref","call","let","case","branch","closure","invoke","foreign"],op)

# Record offsets of one section, in order, and the offset after its last record.
def records(-B: Data, n: Nat, +image: Store, +total: U32, +section: U32, +at: U32, found: List<&2,U32>, next: List<&2,U32> -> U32 -> Result<String,B>) -> Result<String,B>:
  match n:
    case 0n: next(List.reverse(&2,U32,found),at)
    case 1n+m:
      +size = read(image,at)
      unless(B,Bool.or(U32.is_ge(at,total),Bool.or(U32.is_lt(size,2),U32.is_gt(size,U32.sub(total,at)))),
        String.concat(["section ",U32.show(section)," record length"]),u =>
        records(B,m,image,total,section,U32.add(at,size),Con{at,found},next))

def sections(-B: Data, n: Nat, +image: Store, +total: U32, +section: U32, +cursor: U32, found: List<&2,List<&2,U32>>, next: List<&2,List<&2,U32>> -> Result<String,B>) -> Result<String,B>:
  match n:
    case 0n: unless(B,Bool.not(U32.is_eq(cursor,total)),"trailing words",u => next(List.reverse(&2,List<&2,U32>,found)))
    case 1n+m:
      +count = read(image,cursor)
      unless(B,Bool.not(U32.is_eq(read(image,U32.add(5,section)),cursor)),String.concat(["section ",U32.show(section)," offset"]),u =>
      unless(B,U32.is_gt(count,1048576),"record count",u =>
      records(B,U32.to_nat(count),image,total,section,U32.add(cursor,1),Nil{},list => end =>
        sections(B,m,image,total,U32.add(section,1),end,Con{list,found},next))))

def zero_all(bytes: List<&2,U32>) -> Bool:
  match bytes:
    case Nil{}: True{}
    case Con{b,rest}: Bool.and(U32.is_eq(b,0),zero_all(rest))

def ceil4(+size: U32) -> U32:
  U32.add(U32.div(size,4),Bool.pick(U32,U32.is_eq(U32.mod(size,4),0),0,1))

def valid_utf8(bytes: List<&2,U32>) -> Bool:
  Maybe.is_some(&2,List<&2,U32>,scalars(bytes))

def spelled(+bytes: List<&2,U32>, +size: Nat) -> Result<String,List<&2,U32>>:
  +text = List.take(&2,U32,bytes,size)
  unless(List<&2,U32>,Bool.or(Bool.not(zero_all(List.drop(&2,U32,bytes,size))),member(text,0)),"name padding",u =>
  unless(List<&2,U32>,Bool.not(valid_utf8(text)),"name utf-8",u => Done{text}))

def named(+image: Store, +at: U32) -> Result<String,List<&2,U32>>:
  +size = read(image,U32.add(at,1))
  +length = U32.sub(read(image,at),1)
  unless(List<&2,U32>,Bool.or(U32.is_eq(size,0),Bool.not(U32.is_eq(length,U32.add(1,ceil4(size))))),"name length",u =>
    spelled(unpack(slice(U32.to_nat(U32.sub(length,1)),image,U32.add(at,2))),U32.to_nat(size)))

def names(at: List<&2,U32>, +image: Store) -> Result<String,List<&2,List<&2,U32>>>:
  match at:
    case Nil{}: Done{Nil{}}
    case Con{a,rest}:
      then(List<&2,U32>,List<&2,List<&2,U32>>,named(image,a),name =>
        then(List<&2,List<&2,U32>>,List<&2,List<&2,U32>>,names(rest,image),more => Done{Con{name,more}}))

def listed(xs: List<&2,List<&2,U32>>, +x: List<&2,U32>) -> Bool:
  match xs:
    case Nil{}: False{}
    case Con{y,rest}: Bool.or(same(x,y),listed(rest,x))

def repeated(xs: List<&2,List<&2,U32>>) -> Bool:
  match xs:
    case Nil{}: False{}
    case Con{+x,+rest}: Bool.or(listed(rest,x),repeated(rest))

def name_at(names: List<&2,List<&2,U32>>, +i: U32) -> Result<String,List<&2,U32>>:
  match names:
    case Nil{}: Fail{"name index"}
    case Con{+name,+rest}: choose(Result<String,List<&2,U32>>,U32.is_eq(i,0),u => Done{name},u => name_at(rest,U32.sub(i,1)))

def reference(+i: U32, +bound: U32) -> Result<String,U32>:
  choose(Result<String,U32>,Bool.and(Bool.not(is_none(i)),U32.is_ge(i,bound)),u => Fail{"type index"},u => Done{i})

def references(words: List<&2,U32>, +bound: U32) -> Result<String,List<&2,U32>>:
  match words:
    case Nil{}: Done{Nil{}}
    case Con{w,rest}:
      then(U32,List<&2,U32>,reference(w,bound),x =>
        then(List<&2,U32>,List<&2,U32>,references(rest,bound),xs => Done{Con{x,xs}}))

# A type row before its constructors are placed: an algebraic row keeps its
# first constructor index and count.
type Row is Data:
  Declared{name: List<&2,U32>, first: U32, count: U32}
  Signature{sort: Sort}

def arrow(live: Bool, domain: U32, result: U32) -> Sort:
  match live:
    case True{}: Arrow{domain,result}
    case False{}: Erased{domain,result}

def width(row: Row) -> U32:
  match row:
    case Declared{name,first,count}: count
    case Signature{sort}: 0

def typed(+image: Store, +names: List<&2,List<&2,U32>>, +bound: U32, +at: U32, +expect: U32) -> Result<String,Row>:
  +kind = read(image,U32.add(at,1))
  +name = read(image,U32.add(at,2))
  +a = read(image,U32.add(at,3))
  +b = read(image,U32.add(at,4))
  unless(Row,Bool.or(Bool.not(U32.is_eq(read(image,at),5)),U32.is_ge(kind,4)),"type record",u =>
    choose(Result<String,Row>,U32.is_eq(kind,0),
      u => unless(Row,Bool.not(U32.is_eq(a,expect)),"constructor grouping",u =>
             then(List<&2,U32>,Row,name_at(names,name),t => Done{Declared{t,a,b}})),
      u => choose(Result<String,Row>,U32.is_eq(kind,3),
        u => unless(Row,Bool.or(Bool.not(U32.is_eq(a,0)),Bool.not(U32.is_eq(b,0))),"opaque type",u =>
               then(List<&2,U32>,Row,name_at(names,name),t => Done{Signature{Opaque{t}}})),
        u => unless(Row,Bool.not(is_none(name)),"arrow name",u =>
               then(U32,Row,reference(a,bound),d =>
                 then(U32,Row,reference(b,bound),r => Done{Signature{arrow(U32.is_eq(kind,1),d,r)}}))))))

def rows(at: List<&2,U32>, +image: Store, +names: List<&2,List<&2,U32>>, +bound: U32, +expect: U32) -> Result<String,List<&2,Row>>:
  match at:
    case Nil{}: Done{Nil{}}
    case Con{a,rest}:
      then(Row,List<&2,Row>,typed(image,names,bound,a,expect),+row =>
        then(List<&2,Row>,List<&2,Row>,rows(rest,image,names,bound,U32.add(expect,width(row))),more => Done{Con{row,more}}))

def widths(rows: List<&2,Row>) -> U32:
  match rows:
    case Nil{}: 0
    case Con{row,rest}: U32.add(width(row),widths(rest))

def slot_of(row: Row, +tag: U32) -> U32:
  match row:
    case Declared{name,+first,+count}: choose(U32,U32.is_lt(tag,count),u => U32.add(first,tag),u => none())
    case Signature{sort}: none()

# The global constructor position of `tag` in type row `t`, or none.
def position(rows: List<&2,Row>, +t: U32, +tag: U32) -> U32:
  match rows:
    case Nil{}: none()
    case Con{row,rest}: choose(U32,U32.is_eq(t,0),u => slot_of(row,tag),u => position(rest,U32.sub(t,1),tag))

# Constructor records fill their row positions; `filled` maps a position to
# its record offset plus one.
def placed(at: List<&2,U32>, +image: Store, +names: List<&2,List<&2,U32>>, +rows: List<&2,Row>, +bound: U32, +filled: Store) -> Result<String,Store>:
  match at:
    case Nil{}: Done{filled}
    case Con{+a,rest}:
      +length = U32.sub(read(image,a),1)
      +place = position(rows,read(image,U32.add(a,1)),read(image,U32.add(a,2)))
      unless(Store,Bool.or(U32.is_lt(length,4),Bool.or(Bool.not(U32.is_eq(length,U32.add(4,read(image,U32.add(a,4))))),U32.is_ge(read(image,U32.add(a,1)),bound))),"constructor record",u =>
      unless(Store,Bool.or(is_none(place),Bool.not(U32.is_eq(read(filled,place),0))),"constructor tag",u =>
      then(List<&2,U32>,Store,name_at(names,read(image,U32.add(a,3))),t =>
      then(List<&2,U32>,Store,references(slice(U32.to_nat(read(image,U32.add(a,4))),image,U32.add(a,5)),bound),fields =>
        placed(rest,image,names,rows,bound,write(filled,place,U32.add(a,1)))))))

def constructor(+image: Store, +names: List<&2,List<&2,U32>>, +at: U32) -> Constructor:
  Constructor{Result.default(&1,&1,String,List<&2,U32>,name_at(names,read(image,U32.add(at,3))),Nil{}),slice(U32.to_nat(read(image,U32.add(at,4))),image,U32.add(at,5))}

def constructors(n: Nat, +image: Store, +names: List<&2,List<&2,U32>>, +filled: Store, +place: U32) -> List<&2,Constructor>:
  match n:
    case 0n: Nil{}
    case 1n+m: Con{constructor(image,names,U32.sub(read(filled,place),1)),constructors(m,image,names,filled,U32.add(place,1))}

def sorted_row(row: Row, +image: Store, +names: List<&2,List<&2,U32>>, +filled: Store) -> Sort:
  match row:
    case Declared{name,+first,+count}: Algebraic{name,constructors(U32.to_nat(count),image,names,filled,first)}
    case Signature{sort}: sort

def sorts(rows: List<&2,Row>, +image: Store, +names: List<&2,List<&2,U32>>, +filled: Store) -> List<&2,Sort>:
  match rows:
    case Nil{}: Nil{}
    case Con{row,rest}: Con{sorted_row(row,image,names,filled),sorts(rest,image,names,filled)}

def constants(at: List<&2,U32>, +image: Store) -> Result<String,List<&2,Constant>>:
  match at:
    case Nil{}: Done{Nil{}}
    case Con{+a,rest}:
      +length = U32.sub(read(image,a),1)
      +kind = read(image,U32.add(a,1))
      +n = read(image,U32.add(a,2))
      unless(List<&2,Constant>,Bool.or(U32.is_lt(length,2),Bool.or(U32.is_ge(kind,4),Bool.not(U32.is_eq(length,U32.add(2,n))))),"constant record",u =>
      unless(List<&2,Constant>,Bool.and(Bool.not(U32.is_eq(kind,3)),Bool.not(U32.is_eq(n,1))),"scalar constant width",u =>
      then(List<&2,Constant>,List<&2,Constant>,constants(rest,image),more =>
        Done{Con{Constant{kind,slice(U32.to_nat(n),image,U32.add(a,3))},more}})))

# Record lengths of SPEC §3: fixed forms, variadic forms, Case and Closure.
def misshaped(+op: U32, +x: U32, +image: Store, +at: U32) -> Bool:
  +x1 = read(image,U32.add(at,4))
  +x2 = read(image,U32.add(at,5))
  +x3 = read(image,U32.add(at,6))
  choose(Bool,Bool.or(Bool.or(U32.is_eq(op,0),U32.is_eq(op,3)),Bool.or(U32.is_eq(op,5),U32.is_eq(op,2))),u => Bool.not(U32.is_eq(x,1)),u =>
  choose(Bool,U32.is_eq(op,7),u => Bool.not(U32.is_eq(x,3)),u =>
  choose(Bool,U32.is_eq(op,9),u => Bool.not(U32.is_eq(x,4)),u =>
  choose(Bool,U32.is_eq(op,8),u =>
    Bool.or(U32.is_lt(x,4),Bool.or(U32.is_ge(x2,2),Bool.or(U32.is_gt(x3,x),
      Bool.not(U32.is_eq(x,U32.add(5,U32.mul(x3,Bool.pick(U32,U32.is_eq(x2,0),1,2)))))))),u =>
  choose(Bool,U32.is_eq(op,10),u => Bool.or(U32.is_lt(x,5),Bool.not(U32.is_eq(x,U32.add(5,x3)))),u =>
    Bool.or(U32.is_lt(x,2),Bool.not(U32.is_eq(x,U32.add(2,x1)))))))))

def shaped(at: List<&2,U32>, +image: Store, starts: Store) -> Result<String,Store>:
  match at:
    case Nil{}: Done{starts}
    case Con{+a,rest}:
      +length = U32.sub(read(image,a),1)
      +op = read(image,U32.add(a,1))
      unless(Store,Bool.or(U32.is_lt(length,2),U32.is_ge(op,13)),"node record",u =>
      unless(Store,misshaped(op,U32.sub(length,2),image,a),String.append(opcode_name(op)," length"),u =>
        shaped(rest,image,write(starts,a,1))))

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
  Claims{marks: Store, owned: U32, roots: U32}

type Env is Data:
  Env{image: Store, starts: Store, types: U32, constants: List<&2,Constant>}

def image_of(env: Env) -> Store:
  match env:
    case Env{image,starts,types,constants}: image

def types_of(env: Env) -> U32:
  match env:
    case Env{image,starts,types,constants}: types

def claim(+env: Env, +parent: U32, +at: U32, +claims: Claims) -> Result<String,Claims>:
  match env claims:
    case Env{image,+starts,types,constants} Claims{+marks,+owned,+roots}:
      choose(Result<String,Claims>,is_none(parent),u => Done{Claims{marks,owned,roots}},u =>
      unless(Claims,U32.is_eq(read(starts,at),0),"child offset",u =>
      unless(Claims,U32.is_ge(at,parent),"child after parent",u =>
      unless(Claims,U32.is_eq(U32.and(read(marks,at),1),1),"shared node",u =>
        Done{Claims{write(marks,at,U32.add(read(marks,at),1)),U32.add(owned,1),roots}}))))

def rooted(+env: Env, +at: U32, +claims: Claims) -> Result<String,Claims>:
  match env claims:
    case Env{image,+starts,types,constants} Claims{+marks,+owned,+roots}:
      unless(Claims,Bool.or(U32.is_eq(read(starts,at),0),Bool.not(U32.is_eq(read(marks,at),0))),"function root",u =>
        Done{Claims{write(marks,at,2),owned,U32.add(roots,1)}})

def is_arm(+op: U32) -> Bool:
  Bool.or(U32.is_eq(op,2),U32.is_eq(op,9))

def is_operand(role: Role) -> Bool:
  match role:
    case Operand{}: True{}
    case _: False{}

def inspected(+env: Env, +at: U32, role: Role) -> Result<String,Unit>:
  match env:
    case Env{+image,starts,+types,+constants}:
      +t = read(image,U32.add(at,2))
      +op = read(image,U32.add(at,1))
      unless(Unit,Bool.and(Bool.not(is_none(t)),U32.is_ge(t,types)),"type index",u =>
      unless(Unit,Bool.and(is_arm(op),is_operand(role)),"standalone arm",u =>
      unless(Unit,Bool.and(U32.is_eq(op,0),U32.is_ge(read(image,U32.add(at,3)),count(Constant,constants))),"constant index",u =>
        Done{Unit{}})))

def operands(words: List<&2,U32>) -> List<&2,Job>:
  match words:
    case Nil{}: Nil{}
    case Con{w,rest}: Con{Job{w,Operand{}},operands(rest)}

def tag_rows(words: List<&2,U32>) -> List<&2,Job>:
  match words:
    case Nil{}: Nil{}
    case Con{+w,+rest}: choose(List<&2,Job>,is_none(w),u => tag_rows(rest),u => Con{Job{w,Tagged{}},tag_rows(rest)})

def key_rows(n: Nat, +image: Store, +at: U32) -> List<&2,Job>:
  match n:
    case 0n: Nil{}
    case 1n+m: Con{Job{read(image,U32.add(at,1)),Keyed{read(image,at)}},key_rows(m,image,U32.add(at,2))}

def fallback(+w: U32) -> List<&2,Job>:
  choose(List<&2,Job>,is_none(w),u => Nil{},u => [Job{w,Fallback{}}])

def operand_jobs(+image: Store, +x: U32) -> List<&2,Job>:
  operands(slice(U32.to_nat(read(image,U32.add(x,1))),image,U32.add(x,2)))

# Children in SPEC §3 order; an absent row or default has no record.
def children(op: Nat, +image: Store, +x: U32, +last: U32) -> List<&2,Job>:
  match op:
    case 1n: operand_jobs(image,x)
    case 2n: operands([read(image,x)])
    case 4n: operand_jobs(image,x)
    case 6n: operand_jobs(image,x)
    case 7n: operands([read(image,U32.add(x,1)),read(image,U32.add(x,2))])
    case 8n:
      +n = read(image,U32.add(x,3))
      List.append(&2,Job,choose(List<&2,Job>,U32.is_eq(read(image,U32.add(x,2)),0),
        u => tag_rows(slice(U32.to_nat(n),image,U32.add(x,4))),
        u => key_rows(U32.to_nat(n),image,U32.add(x,4))),fallback(last))
    case 9n: operands([read(image,U32.add(x,3))])
    case 10n: operands([last])
    case 11n: Con{Job{read(image,x),Operand{}},operand_jobs(image,x)}
    case 12n: operand_jobs(image,x)
    case _: Nil{}

def kids(+image: Store, +at: U32) -> List<&2,Job>:
  children(U32.to_nat(read(image,U32.add(at,1))),image,U32.add(at,3),read(image,U32.sub(U32.add(at,read(image,at)),1)))

def blank() -> Node:
  Value{none(),none()}

def first(nodes: List<&2,Node>) -> Node:
  match nodes:
    case Nil{}: blank()
    case Con{node,rest}: node

def second(nodes: List<&2,Node>) -> Node:
  match nodes:
    case Con{a,Con{b,rest}}: b
    case _: blank()

def rest_of(nodes: List<&2,Node>) -> List<&2,Node>:
  match nodes:
    case Nil{}: Nil{}
    case Con{node,rest}: rest

def final(nodes: List<&2,Node>) -> Node:
  match nodes:
    case Nil{}: blank()
    case Con{node,Nil{}}: node
    case Con{node,rest}: final(rest)

def constant_at(constants: List<&2,Constant>, +i: U32) -> Constant:
  match constants:
    case Nil{}: Constant{none(),Nil{}}
    case Con{+c,+rest}: choose(Constant,U32.is_eq(i,0),u => c,u => constant_at(rest,U32.sub(i,1)))

def filled_rows(words: List<&2,U32>, nodes: List<&2,Node>) -> List<&2,Maybe<&2,Node>>:
  match words nodes:
    case Nil{} _: Nil{}
    case Con{+w,+rest} Con{+node,+more}:
      choose(List<&2,Maybe<&2,Node>>,is_none(w),u => Con{None{},filled_rows(rest,Con{node,more})},u => Con{Some{node},filled_rows(rest,more)})
    case Con{w,rest} Nil{}: Con{None{},filled_rows(rest,Nil{})}

def keyed_rows(n: Nat, nodes: List<&2,Node>) -> List<&2,Maybe<&2,Node>>:
  match n nodes:
    case 1n+m Con{node,more}: Con{Some{node},keyed_rows(m,more)}
    case _ _: Nil{}

def is_branch(node: Node) -> Bool:
  match node:
    case Branch{key,first,fields,body}: True{}
    case _: False{}

def is_default(node: Node) -> Bool:
  match node:
    case Default{body}: True{}
    case _: False{}

def rows_are_branches(rows: List<&2,Maybe<&2,Node>>) -> Bool:
  match rows:
    case Nil{}: True{}
    case Con{None{},rest}: rows_are_branches(rest)
    case Con{Some{node},rest}: Bool.and(is_branch(node),rows_are_branches(rest))

def default_is_default(fallback: Maybe<&2,Node>) -> Bool:
  match fallback:
    case None{}: True{}
    case Some{node}: is_default(node)

def cased(+image: Store, +at: U32, +types: U32, +nodes: List<&2,Node>) -> Result<String,Node>:
  +x = U32.add(at,3)
  +mode = read(image,U32.add(x,2))
  +n = read(image,U32.add(x,3))
  +rows = choose(List<&2,Maybe<&2,Node>>,U32.is_eq(mode,0),u => filled_rows(slice(U32.to_nat(n),image,U32.add(x,4)),nodes),u => keyed_rows(U32.to_nat(n),nodes))
  +fallback = choose(Maybe<&2,Node>,is_none(read(image,U32.sub(U32.add(at,read(image,at)),1))),u => None{},u => Some{final(nodes)})
  unless(Node,Bool.not(Bool.and(rows_are_branches(rows),default_is_default(fallback))),"case arm kind",u =>
    then(U32,Node,reference(read(image,U32.add(x,1)),types),s => Done{Case{read(image,U32.add(at,2)),read(image,x),s,mode,rows,fallback}}))

def keyed(role: Role, node: Node) -> Result<String,Node>:
  match role node:
    case Keyed{+k} Branch{+key,first,fields,body}:
      choose(Result<String,Node>,U32.is_eq(key,k),u => Done{Branch{key,first,fields,body}},u => Fail{"case key"})
    case Keyed{k} _: Fail{"case key"}
    case _ _: Done{node}

def built(op: Nat, +image: Store, +types: U32, +constants: List<&2,Constant>, +at: U32, +t: U32, +x0: U32, +x1: U32, +x2: U32, +nodes: List<&2,Node>) -> Result<String,Node>:
  match op:
    case 0n: Done{Literal{t,constant_at(constants,x0)}}
    case 1n: Done{Intrinsic{t,x0,nodes}}
    case 2n: Done{Default{first(nodes)}}
    case 3n: Done{Value{t,x0}}
    case 4n: Done{Construct{t,x0,nodes}}
    case 5n: Done{Reference{t,x0}}
    case 6n: Done{Application{t,x0,nodes}}
    case 7n: Done{Let{t,x0,first(nodes),second(nodes)}}
    case 8n: cased(image,at,types,nodes)
    case 9n: Done{Branch{x0,x1,x2,first(nodes)}}
    case 10n: Done{Closure{t,x1,x2,slice(U32.to_nat(read(image,U32.add(at,6))),image,U32.add(at,7)),first(nodes)}}
    case 11n: Done{Invoke{t,first(nodes),rest_of(nodes)}}
    case 12n: Done{Foreign{t,x0,nodes}}
    case _: Fail{"opcode"}

def assembled(+env: Env, +at: U32, nodes: List<&2,Node>) -> Result<String,Node>:
  match env:
    case Env{+image,starts,+types,+constants}:
      built(U32.to_nat(read(image,U32.add(at,1))),image,types,constants,at,read(image,U32.add(at,2)),
        read(image,U32.add(at,3)),read(image,U32.add(at,4)),read(image,U32.add(at,5)),nodes)

# Post-order trees, each child claimed once and before its parent. Fuel bounds
# the nesting of pending jobs by the image's word count.
def forest(fuel: Nat, +env: Env, +parent: U32, work: List<&2,Job>, claims: Claims, done: List<&2,Node>, next: List<&2,Node> -> Claims -> Result<String,Plan>) -> Result<String,Plan>:
  match fuel work:
    case _ Nil{}: next(List.reverse(&2,Node,done),claims)
    case 0n _: Fail{"node depth"}
    case 1n+ +f Con{Job{+at,+role},rest}:
      then(Claims,Plan,claim(env,parent,at,claims),claims =>
      then(Unit,Plan,inspected(env,at,role),u =>
      forest(f,env,at,kids(image_of(env),at),claims,Nil{},nodes => claims =>
      then(Node,Plan,assembled(env,at,nodes),node =>
      then(Node,Plan,keyed(role,node),node =>
      forest(f,env,parent,rest,claims,Con{node,done},next))))))

def functions(at: List<&2,U32>, +fuel: Nat, +env: Env, +names: List<&2,List<&2,U32>>, claims: Claims, found: List<&2,Function>, next: List<&2,Function> -> Claims -> Result<String,Plan>) -> Result<String,Plan>:
  match at:
    case Nil{}: next(List.reverse(&2,Function,found),claims)
    case Con{+a,rest}:
      +image = image_of(env)
      +length = U32.sub(read(image,a),1)
      +arity = read(image,U32.add(a,3))
      +root = read(image,U32.add(a,5))
      unless(Plan,Bool.or(U32.is_lt(length,5),Bool.not(U32.is_eq(length,U32.add(5,arity)))),"function record",u =>
      then(Claims,Plan,rooted(env,root,claims),claims =>
      then(List<&2,U32>,Plan,name_at(names,read(image,U32.add(a,1))),name =>
      then(List<&2,U32>,Plan,references(slice(U32.to_nat(arity),image,U32.add(a,6)),types_of(env)),parameters =>
      then(U32,Plan,reference(read(image,U32.add(a,2)),types_of(env)),result =>
      forest(fuel,env,none(),[Job{root,Operand{}}],claims,Nil{},nodes => claims =>
        functions(rest,fuel,env,names,claims,Con{Function{name,parameters,result,read(image,U32.add(a,4)),first(nodes)},found},next)))))))

def name_of(f: Function) -> List<&2,U32>:
  match f:
    case Function{name,parameters,result,slots,body}: name

def main_bytes() -> List<&2,U32>:
  [109,97,105,110]

def function_at(functions: List<&2,Function>, +i: U32) -> Maybe<&2,Function>:
  match functions:
    case Nil{}: None{}
    case Con{+f,+rest}: choose(Maybe<&2,Function>,U32.is_eq(i,0),u => Some{f},u => function_at(rest,U32.sub(i,1)))

def names_main(found: Maybe<&2,Function>) -> Bool:
  match found:
    case None{}: False{}
    case Some{f}: same(name_of(f),main_bytes())

def planned(+image: Store, +nodes: U32, +sorts: List<&2,Sort>, +functions: List<&2,Function>, claims: Claims) -> Result<String,Plan>:
  match claims:
    case Claims{marks,owned,roots}:
      +main = read(image,4)
      unless(Plan,Bool.not(U32.is_eq(U32.add(owned,roots),nodes)),"unreachable node",u =>
      unless(Plan,Bool.and(Bool.not(is_none(main)),Bool.not(names_main(function_at(functions,main)))),"main index",u =>
      then(List<&2,U32>,Plan,references(slice(12n,image,12),count(Sort,sorts)),representation =>
        Done{Plan{read(image,3),sorts,functions,representation}})))

def decoded(lists: List<&2,List<&2,U32>>, +image: Store, +total: U32) -> Result<String,Plan>:
  match lists:
    case Con{+t,Con{+c,Con{f,Con{k,Con{+n,Con{m,Nil{}}}}}}}:
      then(List<&2,List<&2,U32>>,Plan,names(m,image),+names =>
      unless(Plan,repeated(names),"duplicate name",u =>
      then(List<&2,Row>,Plan,rows(t,image,names,count(U32,t),0),+rows =>
      unless(Plan,Bool.not(U32.is_eq(widths(rows),count(U32,c))),"constructor count",u =>
      then(Store,Plan,placed(c,image,names,rows,count(U32,t),empty()),+filled =>
      then(List<&2,Constant>,Plan,constants(k,image),+constants =>
      then(Store,Plan,shaped(n,image,empty()),+starts =>
      functions(f,U32.to_nat(total),Env{image,starts,count(U32,t),constants},names,Claims{empty(),0,0},Nil{},found => claims =>
        planned(image,count(U32,n),sorts(rows,image,names,filled),found,claims)))))))))
    case _: Fail{"sections"}

# Header, sections and records of SPEC §2, refused in serializer.decode's order.
def decode(+words: List<&2,U32>) -> Result<String,Plan>:
  +total = count(U32,words)
  +image = stored(words,empty(),0)
  unless(Plan,Bool.or(Bool.not(U32.is_eq(read(image,0),magic())),Bool.not(U32.is_eq(read(image,1),1))),"magic",u =>
  unless(Plan,Bool.not(U32.is_eq(read(image,2),total)),"total",u =>
  unless(Plan,Bool.or(U32.is_ge(read(image,3),2),Bool.not(U32.is_eq(read(image,11),0))),"header",u =>
  unless(Plan,Bool.not(same(slice(8n,image,24),digest())),"registry digest",u =>
    sections(Plan,6n,image,total,0,32,Nil{},lists => decoded(lists,image,total))))))

# ---------------------------------------------------------------- registry

# Representation positions follow header words 12-23.
def rep_name(+r: U32) -> String:
  nth_text(["Nat","U32","Char","String","Bool","Cmp","Unit","List","Result","Sigma","IO.OP","File"],r)

type Primitive is Data:
  Primitive{inputs: List<&2,U32>, output: U32}

def primitive_at(table: List<&2,Primitive>, +id: U32) -> Maybe<&2,Primitive>:
  match table:
    case Nil{}: None{}
    case Con{+p,+rest}: choose(Maybe<&2,Primitive>,U32.is_eq(id,0),u => Some{p},u => primitive_at(rest,U32.sub(id,1)))

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
    case Con{+x,+rest}: choose(List<&2,List<&2,U32>>,U32.is_eq(i,0),u => x,u => nth_fields(rest,U32.sub(i,1)))

# Pinned live field types by constructor: a representation position, or none
# for an erased type parameter. U32 and File are opaque and have no row.
def pinned(+r: U32) -> List<&2,List<&2,U32>>:
  +o = none()
  nth_fields([[[],[0]],[],[[1]],[[],[2,3]],[[],[]],[[],[],[]],[[]],[[],[o,7]],[[o],[o]],[[o,o]],[[o],[1,3]],[]],r)

# ---------------------------------------------------------------- validation

def nth_sort(types: List<&2,Sort>, +t: U32) -> Maybe<&2,Sort>:
  match types:
    case Nil{}: None{}
    case Con{+s,+rest}: choose(Maybe<&2,Sort>,U32.is_eq(t,0),u => Some{s},u => nth_sort(rest,U32.sub(t,1)))

# Kind codes of SPEC §2: 0 algebraic, 1 live arrow, 2 erased arrow, 3 opaque.
def sort_code(sort: Maybe<&2,Sort>) -> U32:
  match sort:
    case None{}: none()
    case Some{Algebraic{name,cs}}: 0
    case Some{Arrow{d,r}}: 1
    case Some{Erased{d,r}}: 2
    case Some{Opaque{name}}: 3

def kind(+types: List<&2,Sort>, +t: U32) -> U32:
  sort_code(nth_sort(types,t))

def sort_constructors(sort: Maybe<&2,Sort>) -> List<&2,Constructor>:
  match sort:
    case Some{Algebraic{name,cs}}: cs
    case _: Nil{}

def constructors_of(+types: List<&2,Sort>, +t: U32) -> List<&2,Constructor>:
  sort_constructors(nth_sort(types,t))

def sort_domain(sort: Maybe<&2,Sort>) -> U32:
  match sort:
    case Some{Arrow{d,r}}: d
    case Some{Erased{d,r}}: d
    case _: none()

def sort_result(sort: Maybe<&2,Sort>) -> U32:
  match sort:
    case Some{Arrow{d,r}}: r
    case Some{Erased{d,r}}: r
    case _: none()

def domain(+types: List<&2,Sort>, +t: U32) -> U32:
  sort_domain(nth_sort(types,t))

def codomain(+types: List<&2,Sort>, +t: U32) -> U32:
  sort_result(nth_sort(types,t))

def fields_of(constructors: List<&2,Constructor>, +tag: U32) -> List<&2,U32>:
  match constructors:
    case Nil{}: Nil{}
    case Con{Constructor{name,+fields},+rest}: choose(List<&2,U32>,U32.is_eq(tag,0),u => fields,u => fields_of(rest,U32.sub(tag,1)))

def is_arrow(+k: U32) -> Bool:
  Bool.or(U32.is_eq(k,1),U32.is_eq(k,2))

# `actual` may flow site `declared` is expected: none fits any type, and arrows
# of one kind fit position by position (SPEC §3).
def fits(fuel: Nat, +types: List<&2,Sort>, +declared: U32, +actual: U32) -> Bool:
  match fuel:
    case 0n: False{}
    case 1n+ +f:
      choose(Bool,Bool.or(Bool.or(is_none(declared),is_none(actual)),U32.is_eq(declared,actual)),u => True{},u =>
      choose(Bool,Bool.and(is_arrow(kind(types,declared)),U32.is_eq(kind(types,declared),kind(types,actual))),u =>
        Bool.and(fits(f,types,domain(types,declared),domain(types,actual)),fits(f,types,codomain(types,declared),codomain(types,actual))),
        u => False{}))

def fit(+types: List<&2,Sort>, +declared: U32, +actual: U32) -> Bool:
  fits(U32.to_nat(U32.add(count(Sort,types),1)),types,declared,actual)

# t is IO(x) = @-R: Type -> (x -> IO.OP<R>) -> IO.OP<R>, with x concrete (SPEC §8).
def is_io(+types: List<&2,Sort>, +op: U32, +t: U32, +x: U32) -> Bool:
  +live = codomain(types,t)
  +k = domain(types,live)
  Bool.and(Bool.and(Bool.not(is_none(x)),Bool.not(is_none(op))),
  Bool.and(Bool.and(U32.is_eq(kind(types,t),2),is_none(domain(types,t))),
  Bool.and(Bool.and(U32.is_eq(kind(types,live),1),U32.is_eq(codomain(types,live),op)),
  Bool.and(U32.is_eq(kind(types,k),1),Bool.and(U32.is_eq(domain(types,k),x),U32.is_eq(codomain(types,k),op))))))

type Context is Data:
  Context{types: List<&2,Sort>, functions: List<&2,Function>, representation: List<&2,U32>}

# An obligation of SPEC §4: check a node in a scope, check a closure or
# function body against its exact slot count, or refuse when `bad`.
type Task is Data:
  Check{node: Node, scope: List<&2,U32>, site: String}
  Nested{node: Node, scope: List<&2,U32>, site: String, slots: U32, owner: String, exact: Bool, fitted: Bool}
  Expect{bad: Bool, message: String}

def at_where(+site: String, what: String) -> String:
  String.concat([site,": ",what])

def type_of(node: Node) -> U32:
  match node:
    case Literal{t,c}: t
    case Intrinsic{t,p,xs}: t
    case Value{t,tag}: t
    case Construct{t,tag,xs}: t
    case Reference{t,slot}: t
    case Application{t,f,xs}: t
    case Let{t,slot,value,body}: t
    case Case{t,slot,s,mode,rows,d}: t
    case Closure{t,live,slots,cs,body}: t
    case Invoke{t,f,xs}: t
    case Foreign{t,id,xs}: t
    case _: none()

def types_of_nodes(nodes: List<&2,Node>) -> List<&2,U32>:
  match nodes:
    case Nil{}: Nil{}
    case Con{node,rest}: Con{type_of(node),types_of_nodes(rest)}

def checked(nodes: List<&2,Node>, +scope: List<&2,U32>, +site: String) -> List<&2,Task>:
  match nodes:
    case Nil{}: Nil{}
    case Con{node,rest}: Con{Check{node,scope,site},checked(rest,scope,site)}

def all_fit(+types: List<&2,Sort>, declared: List<&2,U32>, actual: List<&2,U32>) -> Bool:
  match declared actual:
    case Con{d,ds} Con{a,as}: Bool.and(fit(types,d,a),all_fit(types,ds,as))
    case _ _: True{}

# Operand r of a prim or foreign is the pinned representation `reps[r]`.
def pinned_operands(+reps: List<&2,U32>, +op: String, +site: String, actual: List<&2,U32>, inputs: List<&2,U32>) -> List<&2,Task>:
  match actual inputs:
    case Con{+a,as} Con{+r,rs}:
      Con{Expect{Bool.or(is_none(nth(reps,r)),Bool.not(U32.is_eq(a,nth(reps,r)))),at_where(site,String.concat([op," operand is not the pinned ",rep_name(r)]))},
        pinned_operands(reps,op,site,as,rs)}
    case _ _: Nil{}

def primitive_tasks(+cx: Context, +op: String, +id: U32, +t: U32, +site: String, +actual: List<&2,U32>, entry: Maybe<&2,Primitive>) -> List<&2,Task>:
  match cx entry:
    case _ None{}: [Expect{True{},at_where(site,String.concat(["unknown ",op," id ",U32.show(id)]))}]
    case Context{+types,functions,+reps} Some{Primitive{+inputs,+output}}:
      Con{Expect{Bool.not(U32.is_eq(count(U32,actual),count(U32,inputs))),at_where(site,String.append(op," arity"))},
        List.append(&2,Task,pinned_operands(reps,op,site,actual,inputs),
          choose(List<&2,Task>,String.eq(op,"prim"),
            u => [Expect{Bool.or(is_none(nth(reps,output)),Bool.not(U32.is_eq(t,nth(reps,output)))),at_where(site,String.append("prim result is not the pinned ",rep_name(output)))}],
            u => [Expect{Bool.not(is_io(types,nth(reps,10),t,nth(reps,output))),at_where(site,String.concat(["foreign result is not IO(",rep_name(output),")"]))}]))}

def strictly_below(xs: List<&2,U32>, +bound: U32, +floor: U32, +started: Bool) -> Bool:
  match xs:
    case Nil{}: True{}
    case Con{+x,rest}:
      Bool.and(Bool.and(U32.is_lt(x,bound),Bool.or(Bool.not(started),U32.is_gt(x,floor))),strictly_below(rest,bound,x,True{}))

def increasing(xs: List<&2,U32>) -> Bool:
  strictly_below(xs,none(),0,False{})

def scoped(caps: List<&2,U32>, +scope: List<&2,U32>) -> List<&2,U32>:
  match caps:
    case Nil{}: Nil{}
    case Con{c,rest}: Con{nth(scope,c),scoped(rest,scope)}

def row_nodes(rows: List<&2,Maybe<&2,Node>>) -> List<&2,Node>:
  match rows:
    case Nil{}: Nil{}
    case Con{None{},rest}: row_nodes(rest)
    case Con{Some{node},rest}: Con{node,row_nodes(rest)}

def uses_of(node: Node) -> List<&2,U32>:
  match node:
    case Reference{t,slot}: [slot]
    case Case{t,slot,s,mode,rows,d}: [slot]
    case Closure{t,live,slots,caps,body}: caps
    case _: Nil{}

def parts(node: Node) -> List<&2,Node>:
  match node:
    case Intrinsic{t,p,xs}: xs
    case Default{body}: [body]
    case Construct{t,tag,xs}: xs
    case Application{t,f,xs}: xs
    case Let{t,slot,value,body}: [value,body]
    case Case{t,slot,s,mode,+rows,d}: List.append(&2,Node,row_nodes(rows),row_nodes([d]))
    case Branch{key,first,fields,body}: [body]
    case Invoke{t,f,xs}: Con{f,xs}
    case Foreign{t,id,xs}: xs
    case _: Nil{}

# Slots a body reads directly: references, Case scrutinees and captures of the
# closures it builds, whose own bodies number their slots afresh.
def uses(fuel: Nat, nodes: List<&2,Node>) -> List<&2,U32>:
  match fuel nodes:
    case 1n+ +f Con{+node,rest}: List.append(&2,U32,uses_of(node),List.append(&2,U32,uses(f,parts(node)),uses(f,rest)))
    case _ _: Nil{}

def covers(n: Nat, +used: List<&2,U32>, +i: U32) -> Bool:
  match n:
    case 0n: True{}
    case 1n+m: Bool.and(member(used,i),covers(m,used,U32.add(i,1)))

def first_rep(reps: List<&2,U32>, +t: U32, +k: U32) -> U32:
  match reps:
    case Nil{}: none()
    case Con{+r,rest}: choose(U32,Bool.and(Bool.not(is_none(r)),U32.is_eq(r,t)),u => k,u => first_rep(rest,t,U32.add(k,1)))

# Constant kinds 0 U32, 1 Nat, 2 Char, 3 String name representations 1, 0, 2, 3.
def constant_rep(+kind: U32) -> U32:
  nth([1,0,2,3],kind)

def const_name(+kind: U32) -> String:
  nth_text(["U32","Nat","Char","String"],kind)

def tag_tasks(rows: List<&2,Maybe<&2,Node>>, +cx: Context, +constructors: List<&2,Constructor>, +scope: List<&2,U32>, +depth: U32, +t: U32, +site: String, +tag: U32) -> List<&2,Task>:
  match rows:
    case Nil{}: Nil{}
    case Con{Some{Branch{+key,+first,+fields,+body}},rest}:
      +bound = fields_of(constructors,tag)
      List.append(&2,Task,
        [Expect{Bool.or(Bool.not(U32.is_eq(key,tag)),U32.is_ge(tag,count(Constructor,constructors))),at_where(site,"branch key")},
         Expect{Bool.or(Bool.not(U32.is_eq(first,depth)),Bool.not(U32.is_eq(fields,count(U32,bound)))),at_where(site,"branch binders")},
         Check{body,List.append(&2,U32,scope,bound),site},
         Expect{Bool.not(U32.is_eq(type_of(body),t)),at_where(site,"branch body type")}],
        tag_tasks(rest,cx,constructors,scope,depth,t,site,U32.add(tag,1)))
    case Con{row,rest}: tag_tasks(rest,cx,constructors,scope,depth,t,site,U32.add(tag,1))

def key_tasks(rows: List<&2,Maybe<&2,Node>>, +scope: List<&2,U32>, +depth: U32, +t: U32, +site: String) -> List<&2,Task>:
  match rows:
    case Con{Some{Branch{key,+first,+fields,+body}},rest}:
      List.append(&2,Task,
        [Expect{Bool.or(Bool.not(U32.is_eq(first,depth)),Bool.not(U32.is_eq(fields,0))),at_where(site,"key branch binds nothing")},
         Check{body,scope,site},
         Expect{Bool.not(U32.is_eq(type_of(body),t)),at_where(site,"key branch body type")}],
        key_tasks(rest,scope,depth,t,site))
    case Con{row,rest}: key_tasks(rest,scope,depth,t,site)
    case Nil{}: Nil{}

def keys_of(rows: List<&2,Maybe<&2,Node>>) -> List<&2,U32>:
  match rows:
    case Con{Some{Branch{key,first,fields,body}},rest}: Con{key,keys_of(rest)}
    case Con{row,rest}: keys_of(rest)
    case Nil{}: Nil{}

def all_present(rows: List<&2,Maybe<&2,Node>>) -> Bool:
  match rows:
    case Nil{}: True{}
    case Con{None{},rest}: False{}
    case Con{Some{node},rest}: all_present(rest)

def default_tasks(fallback: Maybe<&2,Node>, +scope: List<&2,U32>, +t: U32, +site: String) -> List<&2,Task>:
  match fallback:
    case Some{Default{+body}}: [Check{body,scope,site},Expect{Bool.not(U32.is_eq(type_of(body),t)),at_where(site,"default body type")}]
    case _: Nil{}

def case_tasks(+cx: Context, +scope: List<&2,U32>, +depth: U32, +site: String, +t: U32, +scrutinee: U32, +mode: U32, +rows: List<&2,Maybe<&2,Node>>, +fallback: Maybe<&2,Node>) -> List<&2,Task>:
  match cx:
    case Context{+types,functions,+reps}:
      +constructors = constructors_of(types,scrutinee)
      List.append(&2,Task,choose(List<&2,Task>,U32.is_eq(mode,0),
        u => List.append(&2,Task,
          [Expect{Bool.not(U32.is_eq(kind(types,scrutinee),0)),at_where(site,"tag case on a non-data type")},
           Expect{Bool.not(U32.is_eq(count(Maybe<&2,Node>,rows),count(Constructor,constructors))),at_where(site,"tag table is not dense")},
           Expect{Bool.xor(Maybe.is_none(&2,Node,fallback),all_present(rows)),at_where(site,"default must cover exactly the missing tags")}],
          tag_tasks(rows,cx,constructors,scope,depth,t,site,0)),
        u => List.append(&2,Task,
          [Expect{Bool.not(Bool.and(Bool.not(is_none(scrutinee)),Bool.or(U32.is_eq(scrutinee,nth(reps,1)),U32.is_eq(scrutinee,nth(reps,2))))),at_where(site,"key case on a non-scalar type")},
           Expect{Bool.or(Bool.not(increasing(keys_of(rows))),Maybe.is_none(&2,Node,fallback)),at_where(site,"keys must increase strictly, with a default")}],
          key_tasks(rows,scope,depth,t,site))),
        default_tasks(fallback,scope,t,site))

def callee(functions: List<&2,Function>, +f: U32) -> Maybe<&2,Function>:
  function_at(functions,f)

def callee_parameters(found: Maybe<&2,Function>) -> List<&2,U32>:
  match found:
    case Some{Function{name,parameters,result,slots,body}}: parameters
    case None{}: Nil{}

def callee_result(found: Maybe<&2,Function>) -> U32:
  match found:
    case Some{Function{name,parameters,result,slots,body}}: result
    case None{}: none()

def codes_text(codes: List<&2,U32>) -> String:
  match codes:
    case Nil{}: SNil{}
    case Con{c,rest}: SCon{Chr{c},codes_text(rest)}

def text_of(bytes: List<&2,U32>) -> String:
  codes_text(Maybe.default(&2,List<&2,U32>,scalars(bytes),Nil{}))

def type_index(+types: List<&2,Sort>, +t: U32, +site: String) -> Task:
  Expect{Bool.and(Bool.not(is_none(t)),U32.is_ge(t,count(Sort,types))),at_where(site,"type index")}

# A node's obligations in the reference validator's order: its own
# preconditions, its children, then what the children's types must satisfy.
def expand(+cx: Context, node: Node, +scope: List<&2,U32>, +depth: U32, +site: String) -> List<&2,Task>:
  match cx node:
    case Context{+types,+functions,+reps} Literal{+t,Constant{+k,data}}:
      [type_index(types,t,site),
       Expect{Bool.not(U32.is_eq(first_rep(reps,t,0),constant_rep(k))),at_where(site,String.concat([const_name(k)," literal at a non-",const_name(k)," type"]))}]
    case Context{+types,+functions,+reps} Value{+t,+tag}:
      [type_index(types,t,site),
       Expect{Bool.or(Bool.not(U32.is_eq(kind(types,t),0)),Bool.or(U32.is_ge(tag,count(Constructor,constructors_of(types,t))),Bool.not(U32.is_eq(count(U32,fields_of(constructors_of(types,t),tag)),0)))),
         at_where(site,"value is not a nullary constructor")}]
    case Context{+types,+functions,+reps} Reference{+t,+slot}:
      [type_index(types,t,site),
       Expect{U32.is_ge(slot,depth),at_where(site,String.concat(["slot ",U32.show(slot)," beyond depth ",U32.show(depth)]))},
       Expect{Bool.not(U32.is_eq(nth(scope,slot),t)),at_where(site,"reference type")}]
    case Context{+types,+functions,+reps} Construct{+t,+tag,+xs}:
      +fields = fields_of(constructors_of(types,t),tag)
      Con{type_index(types,t,site),List.append(&2,Task,checked(xs,scope,site),
        [Expect{Bool.or(Bool.not(U32.is_eq(kind(types,t),0)),U32.is_ge(tag,count(Constructor,constructors_of(types,t)))),at_where(site,"construct tag")},
         Expect{Bool.or(U32.is_eq(count(U32,fields),0),Bool.not(U32.is_eq(count(U32,fields),count(Node,xs)))),at_where(site,"construct arity")},
         Expect{Bool.not(all_fit(types,fields,types_of_nodes(xs))),at_where(site,"construct field type")}])}
    case Context{+types,+functions,+reps} Application{+t,+f,+xs}:
      +found = callee(functions,f)
      Con{type_index(types,t,site),List.append(&2,Task,checked(xs,scope,site),
        [Expect{U32.is_ge(f,count(Function,functions)),at_where(site,"function index")},
         Expect{Bool.not(U32.is_eq(count(Node,xs),count(U32,callee_parameters(found)))),at_where(site,"call arity")},
         Expect{Bool.not(Bool.and(fit(types,callee_result(found),t),all_fit(types,callee_parameters(found),types_of_nodes(xs)))),at_where(site,"call types")}])}
    case Context{+types,+functions,+reps} Intrinsic{+t,+id,+xs}:
      Con{type_index(types,t,site),List.append(&2,Task,checked(xs,scope,site),
        primitive_tasks(Context{types,functions,reps},"prim",id,t,site,types_of_nodes(xs),primitive_at(prims(),id)))}
    case Context{+types,+functions,+reps} Foreign{+t,+id,+xs}:
      Con{type_index(types,t,site),List.append(&2,Task,checked(xs,scope,site),
        primitive_tasks(Context{types,functions,reps},"foreign",id,t,site,types_of_nodes(xs),primitive_at(foreigns(),id)))}
    case Context{+types,+functions,+reps} Let{+t,+slot,+value,+body}:
      [type_index(types,t,site),
       Expect{Bool.not(U32.is_eq(slot,depth)),at_where(site,String.concat(["let slot ",U32.show(slot)," at depth ",U32.show(depth)]))},
       Check{value,scope,site},
       Check{body,List.append(&2,U32,scope,[type_of(value)]),site},
       Expect{Bool.not(U32.is_eq(type_of(body),t)),at_where(site,"let body type")}]
    case Context{+types,+functions,+reps} Case{+t,+slot,+scrutinee,+mode,+rows,+fallback}:
      Con{type_index(types,t,site),
      Con{Expect{U32.is_ge(slot,depth),at_where(site,"case slot beyond depth")},
      Con{Expect{Bool.or(is_none(scrutinee),Bool.not(U32.is_eq(nth(scope,slot),scrutinee))),at_where(site,"case scrutinee type")},
        case_tasks(Context{types,functions,reps},scope,depth,site,t,scrutinee,mode,rows,fallback)}}}
    case Context{+types,+functions,+reps} Closure{+t,+live,+slots,+caps,+body}:
      +arrow = kind(types,t)
      +inner = List.append(&2,U32,scoped(caps,scope),Bool.pick(List<&2,U32>,U32.is_eq(live,1),[domain(types,t)],Nil{}))
      [type_index(types,t,site),
       Expect{Bool.not(Bool.or(Bool.and(U32.is_eq(arrow,1),U32.is_eq(live,1)),Bool.and(U32.is_eq(arrow,2),U32.is_eq(live,0)))),at_where(site,"closure arrow")},
       Expect{Bool.not(strictly_below(caps,depth,0,False{})),at_where(site,"captures must increase strictly below depth")},
       Nested{body,inner,String.append(site,"/closure"),slots,site,
         covers(U32.to_nat(count(U32,caps)),uses(U32.to_nat(none()),[body]),0),fit(types,codomain(types,t),type_of(body))}]
    case Context{+types,+functions,+reps} Invoke{+t,+f,+xs}:
      +g = type_of(f)
      +arrow = kind(types,g)
      Con{type_index(types,t,site),Con{Check{f,scope,site},List.append(&2,Task,checked(xs,scope,site),
        [Expect{Bool.or(Bool.not(is_arrow(arrow)),Bool.not(U32.is_eq(count(Node,xs),Bool.pick(U32,U32.is_eq(arrow,1),1,0)))),at_where(site,"invoke arity")},
         Expect{Bool.or(Bool.not(fit(types,codomain(types,g),t)),Bool.and(Bool.not(U32.is_eq(count(Node,xs),0)),Bool.not(fit(types,domain(types,g),type_of(first(xs)))))),at_where(site,"invoke types")}])}}
    case _ Branch{key,first,fields,body}: [Expect{True{},at_where(site,"standalone branch")}]
    case _ Default{body}: [Expect{True{},at_where(site,"standalone default")}]

def larger(+a: U32, +b: U32) -> U32:
  Bool.pick(U32,U32.is_gt(a,b),a,b)

# Runs obligations in order; the first refused one is the reason. Returns the
# deepest scope reached, excluding nested closure bodies (SPEC §3).
def checks(fuel: Nat, tasks: List<&2,Task>, +cx: Context, +deepest: U32) -> Result<String,U32>:
  match fuel tasks:
    case _ Nil{}: Done{deepest}
    case 0n _: Fail{"validation depth"}
    case 1n+ +f Con{Check{node,+scope,+site},rest}:
      then(U32,U32,checks(f,expand(cx,node,scope,count(U32,scope),site),cx,count(U32,scope)),+d =>
        checks(f,rest,cx,larger(deepest,d)))
    case 1n+ +f Con{Nested{node,+scope,inner,+slots,+owner,exact,fitted},rest}:
      then(U32,U32,checks(f,[Check{node,scope,inner}],cx,count(U32,scope)),+d =>
        unless(U32,Bool.not(exact),at_where(owner,"captures are not exactly the free slots of the body"),u =>
        unless(U32,Bool.not(U32.is_eq(d,slots)),at_where(owner,String.concat(["closure slots ",U32.show(slots),", reached ",U32.show(d)])),u =>
        unless(U32,Bool.not(fitted),at_where(owner,"closure result type"),u => checks(f,rest,cx,deepest)))))
    case 1n+ +f Con{Expect{bad,message},rest}:
      unless(U32,bad,message,u => checks(f,rest,cx,deepest))

def pin(+reps: List<&2,U32>, +spec: U32) -> U32:
  choose(U32,is_none(spec),u => none(),u => nth(reps,spec))

# A pinned field names a declared representation, or is an erased parameter.
def same_fields(+reps: List<&2,U32>, fields: List<&2,U32>, specs: List<&2,U32>) -> Bool:
  match fields specs:
    case Nil{} Nil{}: True{}
    case Con{+f,fs} Con{+s,ss}:
      Bool.and(Bool.and(U32.is_eq(f,pin(reps,s)),Bool.or(is_none(s),Bool.not(is_none(nth(reps,s))))),same_fields(reps,fs,ss))
    case _ _: False{}

def same_shape(+reps: List<&2,U32>, constructors: List<&2,Constructor>, specs: List<&2,List<&2,U32>>) -> Bool:
  match constructors specs:
    case Nil{} Nil{}: True{}
    case Con{Constructor{name,fields},cs} Con{s,ss}: Bool.and(same_fields(reps,fields,s),same_shape(reps,cs,ss))
    case _ _: False{}

def representations(n: Nat, +types: List<&2,Sort>, +reps: List<&2,U32>, +r: U32) -> Result<String,Unit>:
  match n:
    case 0n: Done{Unit{}}
    case 1n+ +m:
      +t = nth(reps,r)
      choose(Result<String,Unit>,is_none(t),u => representations(m,types,reps,U32.add(r,1)),u =>
      choose(Result<String,Unit>,Bool.or(U32.is_eq(r,1),U32.is_eq(r,11)),
        u => unless(Unit,Bool.not(U32.is_eq(kind(types,t),3)),String.concat(["representation: ",rep_name(r)," must be opaque"]),u =>
               representations(m,types,reps,U32.add(r,1))),
        u => unless(Unit,Bool.or(Bool.not(U32.is_eq(kind(types,t),0)),Bool.not(same_shape(reps,constructors_of(types,t),pinned(r)))),
               String.concat(["representation: ",rep_name(r)," shape"]),u => representations(m,types,reps,U32.add(r,1)))))

def function_names(functions: List<&2,Function>) -> List<&2,List<&2,U32>>:
  match functions:
    case Nil{}: Nil{}
    case Con{f,rest}: Con{name_of(f),function_names(rest)}

def nth_bool(xs: List<&2,Bool>, +i: U32) -> Bool:
  match xs:
    case Nil{}: False{}
    case Con{+x,+rest}: choose(Bool,U32.is_eq(i,0),u => x,u => nth_bool(rest,U32.sub(i,1)))

def grounded_at(+marks: List<&2,Bool>, +t: U32) -> Bool:
  Bool.or(is_none(t),nth_bool(marks,t))

def regrounded(sorts: List<&2,Sort>, +marks: List<&2,Bool>, current: List<&2,Bool>) -> List<&2,Bool>:
  match sorts current:
    case Con{Arrow{+d,+r},ss} Con{m,ms}: Con{Bool.or(m,Bool.and(grounded_at(marks,d),grounded_at(marks,r))),regrounded(ss,marks,ms)}
    case Con{Erased{+d,+r},ss} Con{m,ms}: Con{Bool.or(m,Bool.and(grounded_at(marks,d),grounded_at(marks,r))),regrounded(ss,marks,ms)}
    case Con{s,ss} Con{m,ms}: Con{m,regrounded(ss,marks,ms)}
    case _ _: Nil{}

def initial_ground(sorts: List<&2,Sort>) -> List<&2,Bool>:
  match sorts:
    case Nil{}: Nil{}
    case Con{Arrow{d,r},rest}: Con{False{},initial_ground(rest)}
    case Con{Erased{d,r},rest}: Con{False{},initial_ground(rest)}
    case Con{s,rest}: Con{True{},initial_ground(rest)}

def ground(n: Nat, +sorts: List<&2,Sort>, +marks: List<&2,Bool>) -> List<&2,Bool>:
  match n:
    case 0n: marks
    case 1n+m: ground(m,sorts,regrounded(sorts,marks,marks))

def every(xs: List<&2,Bool>) -> Bool:
  match xs:
    case Nil{}: True{}
    case Con{x,rest}: Bool.and(x,every(rest))

# Arrows are grounded once their domain and result are; a cycle never is.
def acyclic(+sorts: List<&2,Sort>) -> Bool:
  every(ground(U32.to_nat(U32.add(count(Sort,sorts),1)),sorts,initial_ground(sorts)))

def named_main(functions: List<&2,Function>) -> Maybe<&2,Function>:
  match functions:
    case Nil{}: None{}
    case Con{+f,+rest}: choose(Maybe<&2,Function>,same(name_of(f),main_bytes()),u => Some{f},u => named_main(rest))

def quoted(names: List<&2,String>) -> String:
  match names:
    case Nil{}: ""
    case Con{n,Nil{}}: String.concat(["'",n,"'"])
    case Con{n,rest}: String.concat(["'",n,"', ",quoted(rest)])

def missing(+reps: List<&2,U32>, wanted: List<&2,U32>) -> List<&2,String>:
  match wanted:
    case Nil{}: Nil{}
    case Con{+r,+rest}: choose(List<&2,String>,is_none(nth(reps,r)),u => Con{rep_name(r),missing(reps,rest)},u => missing(reps,rest))

def main_ready(found: Maybe<&2,Function>) -> Bool:
  match found:
    case Some{Function{name,parameters,result,slots,body}}: U32.is_eq(count(U32,parameters),0)
    case None{}: False{}

def main_returns(+types: List<&2,Sort>, +reps: List<&2,U32>, found: Maybe<&2,Function>) -> Bool:
  match found:
    case Some{Function{name,parameters,+result,slots,body}}: is_io(types,nth(reps,10),result,nth(reps,6))
    case None{}: True{}

# A Program's main takes no live argument and returns IO(Unit) (SPEC §8).
def program_valid(+entry: U32, +cx: Context) -> Result<String,Unit>:
  match cx:
    case Context{+types,+functions,+reps}:
      +absent = missing(reps,[6,3,10])
      choose(Result<String,Unit>,Bool.not(U32.is_eq(entry,1)),u => Done{Unit{}},u =>
      unless(Unit,Bool.not(main_ready(named_main(functions))),"program: main must exist with no live parameters",u =>
      unless(Unit,Bool.not(U32.is_eq(count(String,absent),0)),String.concat(["program: missing representation [",quoted(absent),"]"]),u =>
      unless(Unit,Bool.not(main_returns(types,reps,named_main(functions))),"program: main must return IO(Unit)",u => Done{Unit{}}))))

def types_in(cx: Context) -> List<&2,Sort>:
  match cx:
    case Context{types,functions,reps}: types

def function_valid(+cx: Context, f: Function) -> Result<String,Unit>:
  match f:
    case Function{name,+parameters,+result,+slots,+body}:
      +site = text_of(name)
      unless(Unit,Bool.or(U32.is_gt(count(U32,parameters),4096),U32.is_gt(slots,65536)),at_where(site,"limits"),u =>
      then(U32,Unit,checks(U32.to_nat(none()),[Check{body,parameters,site}],cx,count(U32,parameters)),+d =>
      unless(Unit,Bool.not(U32.is_eq(d,slots)),at_where(site,String.concat(["slots ",U32.show(slots),", reached ",U32.show(d)])),u =>
      unless(Unit,Bool.not(fit(types_in(cx),result,type_of(body))),at_where(site,"body type"),u => Done{Unit{}}))))

def functions_valid(functions: List<&2,Function>, +cx: Context) -> Result<String,Unit>:
  match functions:
    case Nil{}: Done{Unit{}}
    case Con{f,rest}: then(Unit,Unit,function_valid(cx,f),u => functions_valid(rest,cx))

# SPEC §4 rules 4 and 5 on a decoded plan: representations, names, arrows,
# the Program entry, then every function, reachable or not.
def validate(plan: Plan) -> Result<String,Unit>:
  match plan:
    case Plan{+entry,+types,+functions,+reps}:
      +cx : Context = Context{types,functions,reps}
      then(Unit,Unit,representations(12n,types,reps,0),u =>
      unless(Unit,repeated(function_names(functions)),"functions: duplicate function name",u =>
      unless(Unit,Bool.not(acyclic(types)),"types: arrow cycle",u =>
      then(Unit,Unit,program_valid(entry,cx),u => functions_valid(functions,cx)))))

# ---------------------------------------------------------------- encoding

def subtrees(node: Node) -> List<&2,Node>:
  match node:
    case Closure{t,live,slots,caps,body}: [body]
    case _: parts(node)

def record_size(node: Node) -> U32:
  match node:
    case Intrinsic{t,p,xs}: U32.add(5,count(Node,xs))
    case Construct{t,tag,xs}: U32.add(5,count(Node,xs))
    case Application{t,f,xs}: U32.add(5,count(Node,xs))
    case Foreign{t,id,xs}: U32.add(5,count(Node,xs))
    case Invoke{t,f,xs}: U32.add(5,count(Node,xs))
    case Let{t,slot,v,b}: 6
    case Branch{key,first,fields,body}: 7
    case Case{t,slot,s,+mode,rows,d}: U32.add(8,U32.mul(count(Maybe<&2,Node>,rows),Bool.pick(U32,U32.is_eq(mode,0),1,2)))
    case Closure{t,live,slots,caps,body}: U32.add(8,count(U32,caps))
    case _: 4

# Words of the records of these subtrees, children before parents.
def size(fuel: Nat, nodes: List<&2,Node>) -> U32:
  match fuel nodes:
    case 1n+ +f Con{+node,rest}: U32.add(U32.add(record_size(node),size(f,subtrees(node))),size(f,rest))
    case _ _: 0

def is_closure(node: Node) -> U32:
  match node:
    case Closure{t,live,slots,caps,body}: 1
    case _: 0

def closures(fuel: Nat, nodes: List<&2,Node>) -> U32:
  match fuel nodes:
    case 1n+ +f Con{+node,rest}: U32.add(U32.add(is_closure(node),closures(f,subtrees(node))),closures(f,rest))
    case _ _: 0

def is_literal(node: Node) -> List<&2,Constant>:
  match node:
    case Literal{t,c}: [c]
    case _: Nil{}

# Literal constants in node-stream order, repeats included.
def literals(fuel: Nat, nodes: List<&2,Node>) -> List<&2,Constant>:
  match fuel nodes:
    case 1n+ +f Con{+node,rest}: List.append(&2,Constant,List.append(&2,Constant,literals(f,subtrees(node)),is_literal(node)),literals(f,rest))
    case _ _: Nil{}

def same_constant(a: Constant, b: Constant) -> Bool:
  match a b:
    case Constant{ka,da} Constant{kb,db}: Bool.and(U32.is_eq(ka,kb),same(da,db))

def constant_index(constants: List<&2,Constant>, +c: Constant, +i: U32) -> U32:
  match constants:
    case Nil{}: none()
    case Con{+k,rest}: choose(U32,same_constant(k,c),u => i,u => constant_index(rest,c,U32.add(i,1)))

def interned(constants: List<&2,Constant>, +seen: List<&2,Constant>) -> List<&2,Constant>:
  match constants:
    case Nil{}: List.reverse(&2,Constant,seen)
    case Con{+c,rest}: interned(rest,Bool.pick(List<&2,Constant>,is_none(constant_index(seen,c,0)),Con{c,seen},seen))

def root_offsets(fuel: Nat, nodes: List<&2,Node>, +start: U32) -> List<&2,U32>:
  match fuel nodes:
    case 1n+ +f Con{+node,rest}:
      +span = U32.add(size(f,subtrees(node)),record_size(node))
      Con{U32.add(start,size(f,subtrees(node))),root_offsets(f,rest,U32.add(start,span))}
    case _ _: Nil{}

def table(rows: List<&2,Maybe<&2,Node>>, offsets: List<&2,U32>) -> List<&2,U32>:
  match rows offsets:
    case Con{None{},rest} _: Con{none(),table(rest,offsets)}
    case Con{Some{node},rest} Con{o,os}: Con{o,table(rest,os)}
    case _ _: Nil{}

def keyed_table(rows: List<&2,Maybe<&2,Node>>, offsets: List<&2,U32>) -> List<&2,U32>:
  match rows offsets:
    case Con{Some{Branch{key,first,fields,body}},rest} Con{o,os}: Con{key,Con{o,keyed_table(rest,os)}}
    case _ _: Nil{}

def fallback_offset(d: Maybe<&2,Node>, +offsets: List<&2,U32>) -> U32:
  match d:
    case None{}: none()
    case Some{node}: nth(offsets,U32.sub(count(U32,offsets),1))

# The record of one node whose children start at `start` and whose closures
# before it number `site`; an arm records its Case's type.
def own(node: Node, +offsets: List<&2,U32>, +site: U32, +arm: U32, +constants: List<&2,Constant>) -> List<&2,U32>:
  match node:
    case Literal{t,+c}: [4,0,t,constant_index(constants,c,0)]
    case Intrinsic{t,p,+xs}: Con{U32.add(5,count(Node,xs)),Con{1,Con{t,Con{p,Con{count(Node,xs),offsets}}}}}
    case Default{body}: [4,2,arm,nth(offsets,0)]
    case Value{t,tag}: [4,3,t,tag]
    case Construct{t,tag,+xs}: Con{U32.add(5,count(Node,xs)),Con{4,Con{t,Con{tag,Con{count(Node,xs),offsets}}}}}
    case Reference{t,slot}: [4,5,t,slot]
    case Application{t,g,+xs}: Con{U32.add(5,count(Node,xs)),Con{6,Con{t,Con{g,Con{count(Node,xs),offsets}}}}}
    case Let{t,slot,v,b}: [6,7,t,slot,nth(offsets,0),nth(offsets,1)]
    case Case{t,slot,s,+mode,+rows,+d}:
      +n = count(Maybe<&2,Node>,rows)
      Con{U32.add(8,U32.mul(n,Bool.pick(U32,U32.is_eq(mode,0),1,2))),Con{8,Con{t,Con{slot,Con{s,Con{mode,Con{n,
        List.append(&2,U32,choose(List<&2,U32>,U32.is_eq(mode,0),u => table(rows,offsets),u => keyed_table(rows,offsets)),[fallback_offset(d,offsets)])}}}}}}}
    case Branch{key,first,fields,body}: [7,9,arm,key,first,fields,nth(offsets,0)]
    case Closure{t,live,slots,+caps,body}:
      Con{U32.add(8,count(U32,caps)),Con{10,Con{t,Con{site,Con{live,Con{slots,Con{count(U32,caps),List.append(&2,U32,caps,[nth(offsets,0)])}}}}}}}
    case Invoke{t,g,+xs}: Con{U32.add(5,count(Node,xs)),Con{11,Con{t,Con{nth(offsets,0),Con{count(Node,xs),List.drop(&2,U32,offsets,1n)}}}}}
    case Foreign{t,id,+xs}: Con{U32.add(5,count(Node,xs)),Con{12,Con{t,Con{id,Con{count(Node,xs),offsets}}}}}

def arm_type(node: Node) -> U32:
  match node:
    case Case{t,slot,s,mode,rows,d}: t
    case _: none()

# Records of consecutive subtrees starting at `start`, post-order (SPEC §2).
def emit(fuel: Nat, nodes: List<&2,Node>, +start: U32, +site: U32, +arm: U32, +constants: List<&2,Constant>) -> List<&2,U32>:
  match fuel nodes:
    case 1n+ +f Con{+node,rest}:
      +kids = subtrees(node)
      +inner = U32.add(start,size(f,kids))
      List.append(&2,U32,List.append(&2,U32,emit(f,kids,start,site,arm_type(node),constants),
          own(node,root_offsets(f,kids,start),U32.add(site,closures(f,kids)),arm,constants)),
        emit(f,rest,U32.add(inner,record_size(node)),U32.add(site,closures(f,Con{node,Nil{}})),arm,constants))
    case _ _: Nil{}

def node_count(fuel: Nat, nodes: List<&2,Node>) -> U32:
  match fuel nodes:
    case 1n+ +f Con{+node,rest}: U32.add(U32.add(1,node_count(f,subtrees(node))),node_count(f,rest))
    case _ _: 0

def byte_index(names: List<&2,List<&2,U32>>, +x: List<&2,U32>, +i: U32) -> U32:
  match names:
    case Nil{}: none()
    case Con{+n,rest}: choose(U32,same(n,x),u => i,u => byte_index(rest,x,U32.add(i,1)))

def distinct(names: List<&2,List<&2,U32>>, +seen: List<&2,List<&2,U32>>) -> List<&2,List<&2,U32>>:
  match names:
    case Nil{}: List.reverse(&2,List<&2,U32>,seen)
    case Con{+n,rest}: distinct(rest,Bool.pick(List<&2,List<&2,U32>>,is_none(byte_index(seen,n,0)),Con{n,seen},seen))

def sort_names(sorts: List<&2,Sort>) -> List<&2,List<&2,U32>>:
  match sorts:
    case Nil{}: Nil{}
    case Con{Algebraic{name,cs},rest}: Con{name,sort_names(rest)}
    case Con{Opaque{name},rest}: Con{name,sort_names(rest)}
    case Con{s,rest}: sort_names(rest)

def constructor_list_names(cs: List<&2,Constructor>) -> List<&2,List<&2,U32>>:
  match cs:
    case Nil{}: Nil{}
    case Con{Constructor{name,fields},rest}: Con{name,constructor_list_names(rest)}

def constructor_names(sorts: List<&2,Sort>) -> List<&2,List<&2,U32>>:
  match sorts:
    case Nil{}: Nil{}
    case Con{Algebraic{name,cs},rest}: List.append(&2,List<&2,U32>,constructor_list_names(cs),constructor_names(rest))
    case Con{s,rest}: constructor_names(rest)

def type_records(sorts: List<&2,Sort>, +names: List<&2,List<&2,U32>>, +first: U32) -> List<&2,U32>:
  match sorts:
    case Nil{}: Nil{}
    case Con{Algebraic{+name,+cs},rest}: List.append(&2,U32,[5,0,byte_index(names,name,0),first,count(Constructor,cs)],type_records(rest,names,U32.add(first,count(Constructor,cs))))
    case Con{Opaque{+name},rest}: List.append(&2,U32,[5,3,byte_index(names,name,0),0,0],type_records(rest,names,first))
    case Con{Arrow{d,r},rest}: List.append(&2,U32,[5,1,none(),d,r],type_records(rest,names,first))
    case Con{Erased{d,r},rest}: List.append(&2,U32,[5,2,none(),d,r],type_records(rest,names,first))

def constructor_records(cs: List<&2,Constructor>, +names: List<&2,List<&2,U32>>, +t: U32, +tag: U32) -> List<&2,U32>:
  match cs:
    case Nil{}: Nil{}
    case Con{Constructor{+name,+fields},rest}:
      List.append(&2,U32,Con{U32.add(5,count(U32,fields)),Con{t,Con{tag,Con{byte_index(names,name,0),Con{count(U32,fields),fields}}}}},
        constructor_records(rest,names,t,U32.add(tag,1)))

def all_constructor_records(sorts: List<&2,Sort>, +names: List<&2,List<&2,U32>>, +t: U32) -> List<&2,U32>:
  match sorts:
    case Nil{}: Nil{}
    case Con{Algebraic{name,cs},rest}: List.append(&2,U32,constructor_records(cs,names,t,0),all_constructor_records(rest,names,U32.add(t,1)))
    case Con{s,rest}: all_constructor_records(rest,names,U32.add(t,1))

def body_of(f: Function) -> Node:
  match f:
    case Function{name,parameters,result,slots,body}: body

def bodies(functions: List<&2,Function>) -> List<&2,Node>:
  match functions:
    case Nil{}: Nil{}
    case Con{f,rest}: Con{body_of(f),bodies(rest)}

def function_records(functions: List<&2,Function>, +names: List<&2,List<&2,U32>>, roots: List<&2,U32>) -> List<&2,U32>:
  match functions roots:
    case Con{Function{+name,+parameters,result,slots,body},rest} Con{root,more}:
      List.append(&2,U32,Con{U32.add(6,count(U32,parameters)),Con{byte_index(names,name,0),Con{result,Con{count(U32,parameters),Con{slots,Con{root,parameters}}}}}},
        function_records(rest,names,more))
    case _ _: Nil{}

def constant_records(constants: List<&2,Constant>) -> List<&2,U32>:
  match constants:
    case Nil{}: Nil{}
    case Con{Constant{kind,+data},rest}: List.append(&2,U32,Con{U32.add(3,count(U32,data)),Con{kind,Con{count(U32,data),data}}},constant_records(rest))

def padded(+bytes: List<&2,U32>) -> List<&2,U32>:
  List.append(&2,U32,bytes,List.take(&2,U32,[0,0,0],U32.to_nat(U32.mod(U32.sub(4,U32.mod(count(U32,bytes),4)),4))))

def name_records(names: List<&2,List<&2,U32>>) -> List<&2,U32>:
  match names:
    case Nil{}: Nil{}
    case Con{+n,rest}:
      +packed = pack(padded(n))
      List.append(&2,U32,Con{U32.add(2,count(U32,packed)),Con{count(U32,n),packed}},name_records(rest))

def function_index(functions: List<&2,Function>, +x: List<&2,U32>, +i: U32) -> U32:
  match functions:
    case Nil{}: none()
    case Con{f,rest}: choose(U32,same(name_of(f),x),u => i,u => function_index(rest,x,U32.add(i,1)))

def parameter_lists(functions: List<&2,Function>) -> List<&2,List<&2,U32>>:
  match functions:
    case Nil{}: Nil{}
    case Con{Function{name,parameters,result,slots,body},rest}: Con{parameters,parameter_lists(rest)}

# The canonical layout of a plan (SPEC §2): names interned by first use over
# type, constructor and function names; constants by first use in the node
# stream; sections adjacent after the 32-word header.
def encode(plan: Plan) -> List<&2,U32>:
  match plan:
    case Plan{entry,+types,+functions,representation}:
      +fuel = U32.to_nat(none())
      +forest = bodies(functions)
      +names = distinct(List.append(&2,List<&2,U32>,sort_names(types),List.append(&2,List<&2,U32>,constructor_names(types),function_names(functions))),Nil{})
      +constants = interned(literals(fuel,forest),Nil{})
      +type_words : List<&2,U32> = Con{count(Sort,types),type_records(types,names,0)}
      +constructor_words : List<&2,U32> = Con{count(List<&2,U32>,constructor_names(types)),all_constructor_records(types,names,0)}
      +function_size = U32.add(1,U32.add(U32.mul(6,count(Function,functions)),count(U32,List.concat(&2,U32,parameter_lists(functions)))))
      +constant_words : List<&2,U32> = Con{count(Constant,constants),constant_records(constants)}
      +types_at : U32 = 32
      +constructors_at = U32.add(types_at,count(U32,type_words))
      +functions_at = U32.add(constructors_at,count(U32,constructor_words))
      +constants_at = U32.add(functions_at,function_size)
      +nodes_at = U32.add(constants_at,count(U32,constant_words))
      +node_words : List<&2,U32> = Con{node_count(fuel,forest),emit(fuel,forest,U32.add(nodes_at,1),0,none(),constants)}
      +names_at = U32.add(nodes_at,count(U32,node_words))
      +name_words : List<&2,U32> = Con{count(List<&2,U32>,names),name_records(names)}
      +function_words : List<&2,U32> = Con{count(Function,functions),function_records(functions,names,root_offsets(fuel,forest,U32.add(nodes_at,1)))}
      +total = U32.add(names_at,count(U32,name_words))
      List.concat(&2,U32,[[magic(),1,total,entry,function_index(functions,main_bytes(),0),types_at,constructors_at,functions_at,constants_at,nodes_at,names_at,0],
        representation,digest(),type_words,constructor_words,function_words,constant_words,node_words,name_words])

# ---------------------------------------------------------------- loading

# How the machine stops short of an answer (SPEC §11). `Exhausted` keeps its
# host kind and precise cause; `Bound` is the model's own transition bound,
# a harness limit that never excuses the VM.
type Stop is Data:
  Exhausted{kind: U32, cause: String}
  Refused{phase: String, code: String}
  Unsupported{phase: String, code: String}
  Internal{code: String}
  Bound{code: String}

def image_limit() -> U32:
  16777216

def refused(-A: Data, result: Result<String,A>) -> Result<Stop,A>:
  match result:
    case Fail{reason}: Fail{Refused{"image",reason}}
    case Done{value}: Done{value}

def validated(result: Result<String,Unit>) -> Result<String,Unit>:
  match result:
    case Fail{problem}: Fail{String.append("validator: ",problem)}
    case Done{u}: Done{u}

def admitted(+words: List<&2,U32>, +plan: Plan) -> Result<String,Plan>:
  then(Unit,Plan,validated(validate(plan)),u =>
    unless(Plan,Bool.not(same(encode(plan),words)),"noncanonical",u => Done{plan}))

# Words the loader admits: decoded, validated and canonical.
def admit(+words: List<&2,U32>) -> Result<Stop,Plan>:
  refused(Plan,then(Plan,Plan,decode(words),+plan => admitted(words,plan)))

# SPEC §4: size first, then the bytes, the plan's rules and canonicality. The
# loader never runs a body.
def load(+bytes: List<&2,U32>) -> Result<Stop,Plan>:
  +size = count(U32,bytes)
  choose(Result<Stop,Plan>,U32.is_gt(size,image_limit()),u => Fail{Exhausted{2,"image-size"}},u =>
  choose(Result<Stop,Plan>,Bool.or(Bool.not(U32.is_eq(U32.mod(size,4),0)),U32.is_lt(size,128)),u => Fail{Refused{"image","length"}},u =>
    admit(pack(bytes))))

# ---------------------------------------------------------------- words, cells and memory

# Zero marks an empty slot. An immediate is (v << 1) | 1 for v < 2^31; every
# other nonzero word is the 8-byte-aligned address of a cell (SPEC §5).
def immediate(+v: U32) -> U32:
  U32.add(U32.shln(v,1n),1)

def is_pointer(+w: U32) -> Bool:
  Bool.and(Bool.not(U32.is_eq(w,0)),U32.is_eq(U32.and(w,1),0))

def boxed(+v: U32) -> Bool:
  U32.is_ge(v,2147483648)

# In words: the image at byte 4096, the frame region at the next 64 KiB
# boundary, 16 MiB of frames, then the heap up to 4 GiB.
def region_words() -> U32:
  4194304

def memory_words() -> U32:
  1073741824

def heap_base(+total: U32) -> U32:
  U32.add(U32.mul(U32.div(U32.add(U32.add(4096,U32.mul(4,total)),65535),65536),16384),region_words())

# Cell classes: 0 Object, 1 Closure, 2 Big, 3 Action, 4 Activation.
# free[k] heads the LIFO list of free cells of 4 << k words.
type Heap is Data:
  Heap{memory: Store, bump: U32, free: List<&2,U32>}

type Cell is Data:
  Cell{heap: Heap, word: U32}

def memory_of(heap: Heap) -> Store:
  match heap:
    case Heap{memory,bump,free}: memory

def load_word(+heap: Heap, +address: U32, +i: U32) -> U32:
  read(memory_of(heap),U32.add(U32.shrn(address,2n),i))

def stored_word(heap: Heap, +address: U32, +i: U32, word: U32) -> Heap:
  match heap:
    case Heap{memory,bump,free}: Heap{write(memory,U32.add(U32.shrn(address,2n),i),word),bump,free}

def writes(words: List<&2,U32>, memory: Store, +at: U32) -> Store:
  match words:
    case Nil{}: memory
    case Con{w,rest}: writes(rest,write(memory,at,w),U32.add(at,1))

def zeros(n: Nat) -> List<&2,U32>:
  match n:
    case 0n: Nil{}
    case 1n+m: Con{0,zeros(m)}

def replaced(xs: List<&2,U32>, +i: U32, +x: U32) -> List<&2,U32>:
  match xs:
    case Nil{}: Nil{}
    case Con{y,+rest}: choose(List<&2,U32>,U32.is_eq(i,0),u => Con{x,rest},u => Con{y,replaced(rest,U32.sub(i,1),x)})

# The smallest k with 4 << k words holding `words`.
def size_class(fuel: Nat, +words: U32, +k: U32) -> U32:
  match fuel:
    case 0n: k
    case 1n+f: choose(U32,U32.is_ge(U32.shln(4,U32.to_nat(k)),words),u => k,u => size_class(f,words,U32.add(k,1)))

def class_of(+words: U32) -> U32:
  size_class(29n,words,0)

def filled(+memory: Store, +at: U32, +rc: U32, +class: U32, +payload: List<&2,U32>, +words: U32) -> Store:
  writes(List.append(&2,U32,[rc,U32.add(U32.shln(count(U32,payload),3n),class)],List.append(&2,U32,payload,zeros(U32.to_nat(U32.sub(words,U32.add(2,count(U32,payload))))))),memory,at)

# Pop the class's free list, else take the bump pointer; write rc, header,
# payload and zeroed padding. A cell past 4 GiB is heap exhaustion.
def allocate(+heap: Heap, +rc: U32, +class: U32, +payload: List<&2,U32>) -> Result<Stop,Cell>:
  match heap:
    case Heap{+memory,+bump,+free}:
      +k = class_of(U32.add(2,count(U32,payload)))
      +words = U32.shln(4,U32.to_nat(k))
      +head = nth(free,k)
      choose(Result<Stop,Cell>,Bool.not(U32.is_eq(head,0)),
        u => Done{Cell{Heap{filled(memory,U32.shrn(head,2n),rc,class,payload,words),bump,replaced(free,k,read(memory,U32.shrn(head,2n)))},head}},
        u => choose(Result<Stop,Cell>,U32.is_gt(words,U32.sub(memory_words(),bump)),u => Fail{Exhausted{2,"heap"}},
          u => Done{Cell{Heap{filled(memory,bump,rc,class,payload,words),U32.add(bump,words),free},U32.shln(bump,2n)}}))

def alloc(+heap: Heap, +class: U32, +payload: List<&2,U32>) -> Result<Stop,Cell>:
  allocate(heap,1,class,payload)

def bind(-A: Data, -B: Data, result: Result<Stop,A>, next: A -> Result<Stop,B>) -> Result<Stop,B>:
  match result:
    case Fail{stop}: Fail{stop}
    case Done{value}: next(value)

def with_cell(-B: Data, result: Result<Stop,Cell>, next: Heap -> U32 -> Result<Stop,B>) -> Result<Stop,B>:
  match result:
    case Fail{stop}: Fail{stop}
    case Done{Cell{heap,word}}: next(heap,word)

# ---------------------------------------------------------------- reference counts

def rc_of(+heap: Heap, +w: U32) -> U32:
  load_word(heap,w,0)

def mortal(+heap: Heap, +w: U32) -> Bool:
  Bool.and(is_pointer(w),Bool.not(is_none(rc_of(heap,w))))

# dup and drop ignore zero, immediates and immortal cells (SPEC §5).
def dup(+heap: Heap, +w: U32) -> Result<Stop,Heap>:
  +rc = rc_of(heap,w)
  choose(Result<Stop,Heap>,Bool.not(mortal(heap,w)),u => Done{heap},u =>
  choose(Result<Stop,Heap>,U32.is_eq(rc,0),u => Fail{Internal{"dangling pointer"}},u =>
  choose(Result<Stop,Heap>,U32.is_eq(rc,4294967294),u => Fail{Exhausted{2,"RCOverflow"}},u =>
    Done{stored_word(heap,w,0,U32.add(rc,1))})))

def dups(words: List<&2,U32>, +heap: Heap) -> Result<Stop,Heap>:
  match words:
    case Nil{}: Done{heap}
    case Con{+w,rest}: bind(Heap,Heap,dup(heap,w),heap => dups(rest,heap))

# Owning edges: Object fields, Closure captures, Action operands and
# Activation slots; a Big has none. Metadata words are never edges.
def edges(+heap: Heap, +q: U32) -> List<&2,U32>:
  +header = load_word(heap,q,1)
  +length = U32.shrn(header,3n)
  +class = U32.and(header,7)
  +skip = Bool.pick(U32,Bool.or(U32.is_eq(class,1),U32.is_eq(class,3)),1,Bool.pick(U32,U32.is_eq(class,2),length,2))
  slice(U32.to_nat(U32.sub(length,Bool.pick(U32,U32.is_gt(skip,length),length,skip))),memory_of(heap),U32.add(U32.shrn(q,2n),U32.add(2,skip)))

def freed(+heap: Heap, +q: U32) -> Heap:
  match heap:
    case Heap{+memory,bump,+free}:
      +k = class_of(U32.add(2,U32.shrn(read(memory,U32.add(U32.shrn(q,2n),1)),3n)))
      Heap{write(write(memory,U32.shrn(q,2n),nth(free,k)),U32.add(U32.shrn(q,2n),1),U32.shln(4,U32.to_nat(k))),bump,replaced(free,k,q)}

type Pending is Data:
  Pending{heap: Heap, work: List<&2,U32>, size: U32}

def with_pending(-B: Data, result: Result<Stop,Pending>, next: Heap -> List<&2,U32> -> U32 -> Result<Stop,B>) -> Result<Stop,B>:
  match result:
    case Fail{stop}: Fail{stop}
    case Done{Pending{heap,work,size}}: next(heap,work,size)

# Decrement each edge, last to first; a count reaching zero joins the worklist,
# which lives in the frame region's free words.
def decremented(edges: List<&2,U32>, +heap: Heap, +work: List<&2,U32>, +size: U32, +room: U32) -> Result<Stop,Pending>:
  match edges:
    case Nil{}: Done{Pending{heap,work,size}}
    case Con{+e,+rest}:
      +rc = rc_of(heap,e)
      choose(Result<Stop,Pending>,Bool.not(mortal(heap,e)),u => decremented(rest,heap,work,size,room),u =>
      choose(Result<Stop,Pending>,U32.is_eq(rc,0),u => Fail{Internal{"rc underflow"}},u =>
      choose(Result<Stop,Pending>,U32.is_eq(rc,1),
        u => choose(Result<Stop,Pending>,U32.is_ge(size,room),u => Fail{Exhausted{3,"frames"}},
               u => decremented(rest,stored_word(heap,e,0,0),Con{e,work},U32.add(size,1),room)),
        u => decremented(rest,stored_word(heap,e,0,U32.sub(rc,1)),work,size,room))))

def release(fuel: Nat, +heap: Heap, work: List<&2,U32>, +size: U32, +room: U32) -> Result<Stop,Heap>:
  match fuel work:
    case _ Nil{}: Done{heap}
    case 0n _: Fail{Internal{"release fuel"}}
    case 1n+ +f Con{+q,rest}:
      with_pending(Heap,decremented(List.reverse(&2,U32,edges(heap,q)),heap,rest,U32.sub(size,1),room),heap => work => size =>
        release(f,freed(heap,q),work,size,room))

def drop(+heap: Heap, +room: U32, +w: U32) -> Result<Stop,Heap>:
  +rc = rc_of(heap,w)
  choose(Result<Stop,Heap>,Bool.not(mortal(heap,w)),u => Done{heap},u =>
  choose(Result<Stop,Heap>,U32.is_eq(rc,0),u => Fail{Internal{"rc underflow"}},u =>
  choose(Result<Stop,Heap>,U32.is_eq(rc,1),
    u => choose(Result<Stop,Heap>,U32.is_eq(room,0),u => Fail{Exhausted{3,"frames"}},
           u => release(U32.to_nat(memory_words()),stored_word(heap,w,0,0),[w],1,room)),
    u => Done{stored_word(heap,w,0,U32.sub(rc,1))})))

def drops(words: List<&2,U32>, +heap: Heap, +room: U32) -> Result<Stop,Heap>:
  match words:
    case Nil{}: Done{heap}
    case Con{+w,rest}: bind(Heap,Heap,drop(heap,room,w),heap => drops(rest,heap,room))

# ---------------------------------------------------------------- code

# The loaded image: record offsets by table index and the constant pool words.
type Code is Data:
  Code{image: Store, types: Store, constructors: Store, functions: Store, names: Store, pool: Store, representation: List<&2,U32>, terminal: U32}

def code_word(+code: Code, +at: U32) -> U32:
  match code:
    case Code{image,types,constructors,functions,names,pool,reps,terminal}: read(image,at)

def type_record(+code: Code, +t: U32) -> U32:
  match code:
    case Code{image,types,constructors,functions,names,pool,reps,terminal}: read(types,t)

def function_record(+code: Code, +f: U32) -> U32:
  match code:
    case Code{image,types,constructors,functions,names,pool,reps,terminal}: read(functions,f)

def name_record(+code: Code, +n: U32) -> U32:
  match code:
    case Code{image,types,constructors,functions,names,pool,reps,terminal}: read(names,n)

def pool_word(+code: Code, +c: U32) -> U32:
  match code:
    case Code{image,types,constructors,functions,names,pool,reps,terminal}: read(pool,c)

def rep(+code: Code, +r: U32) -> U32:
  match code:
    case Code{image,types,constructors,functions,names,pool,reps,terminal}: nth(reps,r)

def terminal(code: Code) -> U32:
  match code:
    case Code{image,types,constructors,functions,names,pool,reps,terminal}: terminal

def is_rep(+code: Code, +t: U32, +r: U32) -> Bool:
  Bool.and(Bool.not(is_none(t)),U32.is_eq(t,rep(code,r)))

def type_kind(+code: Code, +t: U32) -> U32:
  choose(U32,is_none(t),u => none(),u => code_word(code,U32.add(type_record(code,t),1)))

def constructor_count(+code: Code, +t: U32) -> U32:
  code_word(code,U32.add(type_record(code,t),4))

def constructor_record(+code: Code, +t: U32, +tag: U32) -> U32:
  match code:
    case Code{+image,types,constructors,functions,names,pool,reps,terminal}:
      read(constructors,U32.add(code_word(Code{image,types,constructors,functions,names,pool,reps,terminal},U32.add(read(types,t),3)),tag))

def field_count(+code: Code, +t: U32, +tag: U32) -> U32:
  code_word(code,U32.add(constructor_record(code,t,tag),4))

def field_type(+code: Code, +t: U32, +tag: U32, +i: U32) -> U32:
  code_word(code,U32.add(constructor_record(code,t,tag),U32.add(5,i)))

def node_op(+code: Code, +at: U32) -> Nat:
  U32.to_nat(code_word(code,U32.add(at,1)))

def node_type(+code: Code, +at: U32) -> U32:
  code_word(code,U32.add(at,2))

def operand(+code: Code, +at: U32, +i: U32) -> U32:
  code_word(code,U32.add(at,U32.add(3,i)))

def node_last(+code: Code, +at: U32) -> U32:
  code_word(code,U32.sub(U32.add(at,code_word(code,at)),1))

# ---------------------------------------------------------------- frames

# A frame record is [value[n], node, aux, head] (SPEC §6); `Gather` keeps its
# filled operands newest first and reserves `need` slots.
type Frame is Data:
  Top{phase: U32}
  Gather{node: U32, need: U32, got: List<&2,U32>}
  Bind{node: U32}
  Scope{depth: U32}
  Call{caller: U32}
  InvokeFunction{node: U32}
  InvokeArgument{node: U32, function: U32}

def frame_words(frame: Frame) -> U32:
  match frame:
    case Gather{node,need,got}: U32.add(need,3)
    case Call{caller}: 4
    case InvokeArgument{node,function}: 4
    case _: 3

# The current Activation, the frames newest first, and the words they occupy.
type Stack is Data:
  Stack{act: U32, frames: List<&2,Frame>, top: U32}

def room(stack: Stack) -> U32:
  match stack:
    case Stack{act,frames,top}: U32.sub(region_words(),top)

def act_of(stack: Stack) -> U32:
  match stack:
    case Stack{act,frames,top}: act

def pushed(+stack: Stack, +frame: Frame) -> Result<Stop,Stack>:
  match stack:
    case Stack{act,frames,+top}:
      choose(Result<Stop,Stack>,U32.is_gt(frame_words(frame),U32.sub(region_words(),top)),u => Fail{Exhausted{3,"frames"}},
        u => Done{Stack{act,Con{frame,frames},U32.add(top,frame_words(frame))}})

def with_act(stack: Stack, act: U32) -> Stack:
  match stack:
    case Stack{old,frames,top}: Stack{act,frames,top}

# Activation payload: owner, depth, slot[capacity].
def depth_of(+heap: Heap, +act: U32) -> U32:
  load_word(heap,act,3)

def slot(+heap: Heap, +act: U32, +i: U32) -> U32:
  load_word(heap,act,U32.add(4,i))

def bound(heap: Heap, +act: U32, +i: U32, w: U32) -> Heap:
  stored_word(heap,act,U32.add(4,i),w)

def deepened(heap: Heap, +act: U32, depth: U32) -> Heap:
  stored_word(heap,act,3,depth)

def binds(words: List<&2,U32>, heap: Heap, +act: U32, +i: U32) -> Heap:
  match words:
    case Nil{}: heap
    case Con{w,rest}: binds(rest,bound(heap,act,i,w),act,U32.add(i,1))

# ---------------------------------------------------------------- inspection

def cell_class(+heap: Heap, +w: U32) -> U32:
  U32.and(load_word(heap,w,1),7)

# The word read at type t is of that type (SPEC §6): Nat, U32 and Char admit an
# immediate or a Big cell, File an immediate, and an algebraic type a nullary
# tag or an Object of its own type whose tag has fields.
def admits(+code: Code, +heap: Heap, +t: U32, +w: U32) -> Bool:
  choose(Bool,Bool.or(is_rep(code,t,0),Bool.or(is_rep(code,t,1),is_rep(code,t,2))),
    u => Bool.or(U32.is_eq(U32.and(w,1),1),Bool.and(is_pointer(w),U32.is_eq(cell_class(heap,w),2))),u =>
  choose(Bool,is_rep(code,t,11),u => U32.is_eq(U32.and(w,1),1),u =>
  choose(Bool,Bool.not(U32.is_eq(type_kind(code,t),0)),u => False{},u =>
  choose(Bool,U32.is_eq(U32.and(w,1),1),
    u => Bool.and(U32.is_lt(U32.shrn(w,1n),constructor_count(code,t)),U32.is_eq(field_count(code,t,U32.shrn(w,1n)),0)),
    u => Bool.and(Bool.and(is_pointer(w),U32.is_eq(cell_class(heap,w),0)),
          Bool.and(U32.is_eq(load_word(heap,w,2),t),
          Bool.and(U32.is_lt(load_word(heap,w,3),constructor_count(code,t)),Bool.not(U32.is_eq(field_count(code,t,load_word(heap,w,3)),0)))))))))

def ill_typed(-A: Data) -> Result<Stop,A>:
  Fail{Refused{"image","ill-typed"}}

def inspected_at(-A: Data, +code: Code, +heap: Heap, +t: U32, +w: U32, next: Unit -> Result<Stop,A>) -> Result<Stop,A>:
  choose(Result<Stop,A>,admits(code,heap,t,w),next,u => ill_typed(A))

# The value of a Nat, U32 or Char word, and the canonical word of a value.
def scalar(+heap: Heap, +w: U32) -> U32:
  choose(U32,U32.is_eq(U32.and(w,1),1),u => U32.shrn(w,1n),u => load_word(heap,w,2))

def word_of(+heap: Heap, +v: U32) -> Result<Stop,Cell>:
  choose(Result<Stop,Cell>,boxed(v),u => alloc(heap,2,[v]),u => Done{Cell{heap,immediate(v)}})

def tag_of(+code: Code, +heap: Heap, +t: U32, +w: U32) -> U32:
  choose(U32,is_rep(code,t,0),u => Bool.pick(U32,U32.is_eq(scalar(heap,w),0),0,1),u =>
    choose(U32,U32.is_eq(U32.and(w,1),1),u => U32.shrn(w,1n),u => load_word(heap,w,3)))

# ---------------------------------------------------------------- primitives

def truth(b: Bool) -> U32:
  immediate(Bool.to_u32(b))

def order(+a: U32, +b: U32) -> U32:
  choose(U32,U32.is_lt(a,b),u => 0,u => Bool.pick(U32,U32.is_eq(a,b),1,2))

# Comparison k of is_eq, is_ne, is_lt, is_le, is_gt, is_ge, unsigned.
def compared(+k: U32, +a: U32, +b: U32) -> Bool:
  nth_bool([U32.is_eq(a,b),U32.is_ne(a,b),U32.is_lt(a,b),U32.is_le(a,b),U32.is_gt(a,b),U32.is_ge(a,b)],k)

def shifted(left: Bool, +a: U32, +n: U32) -> U32:
  choose(U32,U32.is_ge(n,32),u => 0,u => Bool.pick(U32,left,U32.shln(a,U32.to_nat(n)),U32.shrn(a,U32.to_nat(n))))

def spaced(+c: U32) -> Bool:
  Bool.or(within(c,9,13),U32.is_eq(c,32))

def digits(fuel: Nat, +v: U32, +acc: List<&2,U32>) -> List<&2,U32>:
  match fuel:
    case 0n: acc
    case 1n+f: choose(List<&2,U32>,U32.is_lt(v,10),u => Con{U32.add(48,v),acc},u => digits(f,U32.div(v,10),Con{U32.add(48,U32.mod(v,10)),acc}))

def code_words(codes: List<&2,U32>) -> List<&2,U32>:
  match codes:
    case Nil{}: Nil{}
    case Con{c,rest}: Con{immediate(c),code_words(rest)}

# The Char words of a String, each cell inspected at String and each
# character at Char.
def chars(fuel: Nat, +code: Code, +heap: Heap, +w: U32) -> Result<Stop,List<&2,U32>>:
  match fuel:
    case 0n: Fail{Internal{"string fuel"}}
    case 1n+f:
      inspected_at(List<&2,U32>,code,heap,rep(code,3),w,u =>
      choose(Result<Stop,List<&2,U32>>,U32.is_eq(U32.and(w,1),1),u => Done{Nil{}},u =>
      inspected_at(List<&2,U32>,code,heap,rep(code,2),load_word(heap,w,4),u =>
        bind(List<&2,U32>,List<&2,U32>,chars(f,code,heap,load_word(heap,w,5)),rest => Done{Con{load_word(heap,w,4),rest}}))))

def string_of(+code: Code, +heap: Heap, +w: U32) -> Result<Stop,List<&2,U32>>:
  chars(U32.to_nat(memory_words()),code,heap,w)

def scalars_of(words: List<&2,U32>, +heap: Heap) -> List<&2,U32>:
  match words:
    case Nil{}: Nil{}
    case Con{w,rest}: Con{scalar(heap,w),scalars_of(rest,heap)}

# SCon cells from the chain's last character to its first, each holding a
# new reference to its character.
def chain(last_first: List<&2,U32>, +code: Code, +heap: Heap, +tail: U32) -> Result<Stop,Cell>:
  match last_first:
    case Nil{}: Done{Cell{heap,tail}}
    case Con{+c,rest}:
      bind(Heap,Cell,dup(heap,c),heap =>
        with_cell(Cell,alloc(heap,0,[rep(code,3),1,c,tail]),heap => w => chain(rest,code,heap,w)))

# Nat results are checked before narrowing: above 2^32-1 is NatRange.
def nat_sum(+heap: Heap, +a: U32, +b: U32) -> Result<Stop,Cell>:
  choose(Result<Stop,Cell>,U32.is_gt(b,U32.sub(none(),a)),u => Fail{Exhausted{2,"NatRange"}},u => word_of(heap,U32.add(a,b)))

def nat_product(+heap: Heap, +a: U32, +b: U32) -> Result<Stop,Cell>:
  choose(Result<Stop,Cell>,Bool.and(Bool.not(U32.is_eq(a,0)),U32.is_gt(b,U32.div(none(),a))),u => Fail{Exhausted{2,"NatRange"}},u => word_of(heap,U32.mul(a,b)))

def immediate_cell(+heap: Heap, +w: U32) -> Result<Stop,Cell>:
  Done{Cell{heap,w}}

def string_cell(+code: Code, +heap: Heap, +w: U32, next: List<&2,U32> -> Result<Stop,Cell>) -> Result<Stop,Cell>:
  bind(List<&2,U32>,Cell,string_of(code,heap,w),next)

# SPEC §9 on inspected operand words `a` and `b`; the result is allocated
# before any operand is dropped.
def computed(id: Nat, +code: Code, +heap: Heap, +a: U32, +b: U32, +x: U32, +y: U32) -> Result<Stop,Cell>:
  match id:
    case 0n: word_of(heap,U32.add(x,y))
    case 1n: word_of(heap,U32.sub(x,y))
    case 2n: word_of(heap,U32.mul(x,y))
    case 3n: word_of(heap,choose(U32,U32.is_eq(y,0),u => 0,u => U32.div(x,y)))
    case 4n: word_of(heap,choose(U32,U32.is_eq(y,0),u => x,u => U32.mod(x,y)))
    case 5n: word_of(heap,U32.not(x))
    case 6n: word_of(heap,U32.and(x,y))
    case 7n: immediate_cell(heap,immediate(order(x,y)))
    case 8n: immediate_cell(heap,truth(compared(0,x,y)))
    case 9n: immediate_cell(heap,truth(compared(1,x,y)))
    case 10n: immediate_cell(heap,truth(compared(2,x,y)))
    case 11n: immediate_cell(heap,truth(compared(3,x,y)))
    case 12n: immediate_cell(heap,truth(compared(4,x,y)))
    case 13n: immediate_cell(heap,truth(compared(5,x,y)))
    case 14n: word_of(heap,shifted(True{},x,y))
    case 15n: word_of(heap,shifted(False{},x,y))
    case 16n: immediate_cell(heap,a)
    case 17n: immediate_cell(heap,a)
    case 18n: immediate_cell(heap,a)
    case 19n: immediate_cell(heap,a)
    case 20n: immediate_cell(heap,truth(U32.is_eq(x,y)))
    case 21n: immediate_cell(heap,truth(spaced(x)))
    case 22n: nat_sum(heap,x,y)
    case 23n: word_of(heap,choose(U32,U32.is_lt(x,y),u => 0,u => U32.sub(x,y)))
    case 24n: nat_product(heap,x,y)
    case 25n: immediate_cell(heap,immediate(order(x,y)))
    case 26n: immediate_cell(heap,truth(compared(0,x,y)))
    case 27n: immediate_cell(heap,truth(compared(1,x,y)))
    case 28n: immediate_cell(heap,truth(compared(2,x,y)))
    case 29n: immediate_cell(heap,truth(compared(3,x,y)))
    case 30n: immediate_cell(heap,truth(compared(4,x,y)))
    case 31n: immediate_cell(heap,truth(compared(5,x,y)))
    case 32n: chain(List.reverse(&2,U32,code_words(digits(10n,x,Nil{}))),code,heap,immediate(0))
    case 33n: chain(List.reverse(&2,U32,code_words(digits(10n,x,Nil{}))),code,heap,immediate(0))
    case 34n: string_cell(code,heap,a,s => string_cell(code,heap,b,t => immediate_cell(heap,truth(same(scalars_of(s,heap),scalars_of(t,heap))))))
    case 35n: string_cell(code,heap,a,s => chain(List.reverse(&2,U32,s),code,heap,b))
    case 36n: string_cell(code,heap,a,s => chain(s,code,heap,immediate(0)))
    case 37n: string_cell(code,heap,a,s => word_of(heap,count(U32,s)))
    case 38n: string_cell(code,heap,a,s => immediate_cell(heap,truth(U32.is_eq(count(U32,s),0))))
    case _: Fail{Refused{"image","prim"}}

def compute(+id: U32, +code: Code, +heap: Heap, +a: U32, +b: U32) -> Result<Stop,Cell>:
  computed(U32.to_nat(id),code,heap,a,b,scalar(heap,a),scalar(heap,b))

# Operands the prim moves into its result: append's tail and the word-keeping
# conversions. Every other operand is dropped after the result exists.
def moved(+id: U32, +i: U32) -> Bool:
  Bool.or(Bool.and(U32.is_eq(id,35),U32.is_eq(i,1)),Bool.and(within(id,16,19),U32.is_eq(i,0)))

def dropped_operands(+id: U32, words: List<&2,U32>, +i: U32) -> List<&2,U32>:
  match words:
    case Nil{}: Nil{}
    case Con{+w,+rest}: choose(List<&2,U32>,moved(id,i),u => dropped_operands(id,rest,U32.add(i,1)),u => Con{w,dropped_operands(id,rest,U32.add(i,1))})

def all_admitted(+code: Code, +heap: Heap, words: List<&2,U32>, inputs: List<&2,U32>) -> Bool:
  match words inputs:
    case Con{w,ws} Con{r,rs}: Bool.and(admits(code,heap,rep(code,r),w),all_admitted(code,heap,ws,rs))
    case _ _: True{}

def primitive_inputs(entry: Maybe<&2,Primitive>) -> List<&2,U32>:
  match entry:
    case Some{Primitive{inputs,output}}: inputs
    case None{}: Nil{}

# ---------------------------------------------------------------- the machine

type Target is Data:
  Callee{function: U32}
  Held{word: U32}

# A Book halts Answered, then is Described; a Program Emits or Dies. A stop
# keeps the control it could not advance, whose words stay owned (SPEC §7:
# the pending Enter stays in the state).
type Outcome is Data:
  Answered{word: U32}
  Described{result: U32, tag: U32, tree: List<&2,U32>}
  Emitted{}
  Died{code: U32, message: List<&2,U32>}
  Stopped{stop: Stop, pending: Control}

type Control is Data:
  Eval{node: U32}
  Return{word: U32}
  Enter{target: Target, ops: List<&2,U32>}
  Finished{outcome: Outcome}

type Meter is Data:
  Meter{fuel: U32, calls: U32, quantum: U32}

# `out` holds the printed lines, newest first.
type Machine is Data:
  Machine{control: Control, stack: Stack, heap: Heap, meter: Meter, out: List<&2,List<&2,U32>>}

# A transition's control, frames and heap; fuel and output change only on Enter.
type Next is Data:
  Next{control: Control, stack: Stack, heap: Heap}

def to(control: Control, stack: Stack, heap: Heap) -> Result<Stop,Next>:
  Done{Next{control,stack,heap}}

def then_stack(-B: Data, result: Result<Stop,Stack>, next: Stack -> Result<Stop,B>) -> Result<Stop,B>:
  bind(Stack,B,result,next)

def operands_of(+code: Code, +node: U32, n: Nat, +i: U32) -> List<&2,U32>:
  match n:
    case 0n: Nil{}
    case 1n+m: Con{operand(code,node,i),operands_of(code,node,m,U32.add(i,1))}

def slots_of(+heap: Heap, +act: U32, words: List<&2,U32>) -> List<&2,U32>:
  match words:
    case Nil{}: Nil{}
    case Con{i,rest}: Con{slot(heap,act,i),slots_of(heap,act,rest)}

# Completing a gathered node (SPEC §6): Nat Succ and Char Chr act on words,
# other constructors allocate an Object, prims compute then drop what they did
# not move, a Foreign builds an inert Action, an Application enters its callee.
def completed(+code: Code, +node: U32, +ops: List<&2,U32>, +stack: Stack, +heap: Heap) -> Result<Stop,Next>:
  +t = node_type(code,node)
  +id = operand(code,node,0)
  +a = nth(ops,0)
  choose(Result<Stop,Next>,U32.is_eq(code_word(code,U32.add(node,1)),6),u => to(Enter{Callee{id},ops},stack,heap),u =>
  choose(Result<Stop,Next>,U32.is_eq(code_word(code,U32.add(node,1)),12),u => with_cell(Next,alloc(heap,3,Con{id,ops}),heap => w => to(Return{w},stack,heap)),u =>
  choose(Result<Stop,Next>,U32.is_eq(code_word(code,U32.add(node,1)),1),
    u => choose(Result<Stop,Next>,Bool.not(all_admitted(code,heap,ops,primitive_inputs(primitive_at(prims(),id)))),u => ill_typed(Next),u =>
           with_cell(Next,compute(id,code,heap,a,nth(ops,1)),heap => w =>
             bind(Heap,Next,drops(dropped_operands(id,ops,0),heap,room(stack)),heap => to(Return{w},stack,heap)))),u =>
  choose(Result<Stop,Next>,is_rep(code,t,0),
    u => inspected_at(Next,code,heap,t,a,u =>
           choose(Result<Stop,Next>,U32.is_eq(scalar(heap,a),none()),u => Fail{Exhausted{2,"NatRange"}},u =>
             with_cell(Next,word_of(heap,U32.add(scalar(heap,a),1)),heap => w =>
               bind(Heap,Next,drop(heap,room(stack),a),heap => to(Return{w},stack,heap))))),u =>
  choose(Result<Stop,Next>,is_rep(code,t,2),u => to(Return{a},stack,heap),u =>
    with_cell(Next,alloc(heap,0,Con{t,Con{id,ops}}),heap => w => to(Return{w},stack,heap)))))))

def gathered(+code: Code, +node: U32, +stack: Stack, +heap: Heap) -> Result<Stop,Next>:
  +n = operand(code,node,1)
  choose(Result<Stop,Next>,U32.is_eq(n,0),u => completed(code,node,Nil{},stack,heap),u =>
    then_stack(Next,pushed(stack,Gather{node,n,Nil{}}),stack => to(Eval{operand(code,node,2)},stack,heap)))

# §6.1: the matching row, the key's arm, or else the default.
def row_arm(+code: Code, +node: U32, +tag: U32) -> U32:
  +arm = choose(U32,U32.is_lt(tag,operand(code,node,3)),u => operand(code,node,U32.add(4,tag)),u => none())
  choose(U32,is_none(arm),u => node_last(code,node),u => arm)

def key_arm(n: Nat, +code: Code, +node: U32, +v: U32, +i: U32) -> U32:
  match n:
    case 0n: node_last(code,node)
    case 1n+m:
      choose(U32,U32.is_eq(operand(code,node,U32.add(4,U32.mul(2,i))),v),u => operand(code,node,U32.add(5,U32.mul(2,i))),u =>
        key_arm(m,code,node,v,U32.add(i,1)))

type Fields is Data:
  Fields{heap: Heap, words: List<&2,U32>}

def with_fields(-B: Data, result: Result<Stop,Fields>, next: Heap -> List<&2,U32> -> Result<Stop,B>) -> Result<Stop,B>:
  match result:
    case Fail{stop}: Fail{stop}
    case Done{Fields{heap,words}}: next(heap,words)

# Words a selected Branch binds: a Nat's predecessor is a new word, a Char
# binds its own code word, an Object its fields; each slot owns a reference.
def selected_fields(+code: Code, +heap: Heap, +t: U32, +w: U32, +f: U32) -> Result<Stop,Fields>:
  +fields = slice(U32.to_nat(f),memory_of(heap),U32.add(U32.shrn(w,2n),4))
  choose(Result<Stop,Fields>,is_rep(code,t,0),u => with_cell(Fields,word_of(heap,U32.sub(scalar(heap,w),1)),heap => x => Done{Fields{heap,[x]}}),u =>
  choose(Result<Stop,Fields>,is_rep(code,t,2),u => bind(Heap,Fields,dup(heap,w),heap => Done{Fields{heap,[w]}}),u =>
    bind(Heap,Fields,dups(fields,heap),heap => Done{Fields{heap,fields}})))

def entered_arm(+code: Code, +arm: U32, +t: U32, +w: U32, +stack: Stack, +heap: Heap) -> Result<Stop,Next>:
  +f = operand(code,arm,2)
  +act = act_of(stack)
  choose(Result<Stop,Next>,Bool.or(U32.is_eq(code_word(code,U32.add(arm,1)),2),U32.is_eq(f,0)),
    u => to(Eval{choose(U32,U32.is_eq(code_word(code,U32.add(arm,1)),2),u => operand(code,arm,0),u => operand(code,arm,3))},stack,heap),
    u => with_fields(Next,selected_fields(code,heap,t,w,f),+heap => words =>
           then_stack(Next,pushed(stack,Scope{depth_of(heap,act)}),stack =>
             to(Eval{operand(code,arm,3)},stack,deepened(binds(words,heap,act,depth_of(heap,act)),act,U32.add(depth_of(heap,act),f))))))

def selected(+code: Code, +node: U32, +stack: Stack, +heap: Heap) -> Result<Stop,Next>:
  +t = operand(code,node,1)
  +w = slot(heap,act_of(stack),operand(code,node,0))
  inspected_at(Next,code,heap,t,w,u =>
    entered_arm(code,choose(U32,U32.is_eq(operand(code,node,2),0),
      u => row_arm(code,node,tag_of(code,heap,t,w)),
      u => key_arm(U32.to_nat(operand(code,node,3)),code,node,scalar(heap,w),0)),t,w,stack,heap))

def closed(+code: Code, +node: U32, +stack: Stack, +heap: Heap) -> Result<Stop,Next>:
  +captured = slots_of(heap,act_of(stack),operands_of(code,node,U32.to_nat(operand(code,node,3)),4))
  bind(Heap,Next,dups(captured,heap),heap =>
    with_cell(Next,alloc(heap,1,Con{node,captured}),heap => w => to(Return{w},stack,heap)))

def evaluated(op: Nat, +code: Code, +node: U32, +stack: Stack, +heap: Heap) -> Result<Stop,Next>:
  match op:
    case 0n: to(Return{pool_word(code,operand(code,node,0))},stack,heap)
    case 3n: to(Return{immediate(operand(code,node,0))},stack,heap)
    case 5n:
      +w = slot(heap,act_of(stack),operand(code,node,0))
      bind(Heap,Next,dup(heap,w),heap => to(Return{w},stack,heap))
    case 1n: gathered(code,node,stack,heap)
    case 4n: gathered(code,node,stack,heap)
    case 6n: gathered(code,node,stack,heap)
    case 12n: gathered(code,node,stack,heap)
    case 7n: then_stack(Next,pushed(stack,Bind{node}),stack => to(Eval{operand(code,node,1)},stack,heap))
    case 8n: selected(code,node,stack,heap)
    case 10n: closed(code,node,stack,heap)
    case 11n: then_stack(Next,pushed(stack,InvokeFunction{node}),stack => to(Eval{operand(code,node,0)},stack,heap))
    case _: Fail{Internal{"eval arm"}}

def unwound(n: Nat, +heap: Heap, +act: U32, +i: U32, +room: U32) -> Result<Stop,Heap>:
  match n:
    case 0n: Done{heap}
    case 1n+m: bind(Heap,Heap,drop(heap,room,slot(heap,act,i)),heap => unwound(m,bound(heap,act,i,0),act,U32.sub(i,1),room))

def topped(+code: Code, +phase: U32, +w: U32, +rest: List<&2,Frame>, +top: U32, +heap: Heap) -> Result<Stop,Next>:
  choose(Result<Stop,Next>,U32.is_eq(phase,0),u => to(Finished{Answered{w}},Stack{0,Con{Top{0},rest},top},heap),u =>
  choose(Result<Stop,Next>,U32.is_eq(phase,1),u => to(Enter{Held{w},Nil{}},Stack{0,Con{Top{2},rest},top},heap),u =>
  choose(Result<Stop,Next>,U32.is_eq(phase,2),u => to(Enter{Held{w},[terminal(code)]},Stack{0,Con{Top{3},rest},top},heap),u =>
    inspected_at(Next,code,heap,rep(code,10),w,u =>
      choose(Result<Stop,Next>,U32.is_eq(load_word(heap,w,3),0),
        u => bind(Heap,Next,drop(heap,room(Stack{0,rest,top}),w),heap => to(Finished{Emitted{}},Stack{0,Con{Top{3},rest},top},heap)),
        u => inspected_at(Next,code,heap,rep(code,1),load_word(heap,w,4),u =>
               bind(List<&2,U32>,Next,string_of(code,heap,load_word(heap,w,5)),message =>
               bind(Heap,Next,drop(heap,room(Stack{0,rest,top}),w),heap2 =>
                 to(Finished{Died{scalar(heap,load_word(heap,w,4)),scalars_of(message,heap)}},Stack{0,Con{Top{3},rest},top},heap2)))))))))

# The Return transitions of SPEC §6, by the top frame.
def returned(+code: Code, +w: U32, stack: Stack, +heap: Heap) -> Result<Stop,Next>:
  match stack:
    case Stack{+act,Con{Gather{+node,+need,+got},+rest},+top}:
      +have : List<&2,U32> = Con{w,got}
      choose(Result<Stop,Next>,U32.is_lt(count(U32,have),need),
        u => to(Eval{operand(code,node,U32.add(2,count(U32,have)))},Stack{act,Con{Gather{node,need,have},rest},top},heap),
        u => completed(code,node,List.reverse(&2,U32,have),Stack{act,rest,U32.sub(top,U32.add(need,3))},heap))
    case Stack{+act,Con{Bind{+node},rest},+top}:
      +d = depth_of(heap,act)
      then_stack(Next,pushed(Stack{act,rest,U32.sub(top,3)},Scope{d}),stack =>
        to(Eval{operand(code,node,2)},stack,deepened(bound(heap,act,d,w),act,U32.add(d,1))))
    case Stack{+act,Con{Scope{+saved},rest},+top}:
      +popped : Stack = Stack{act,rest,U32.sub(top,3)}
      +d = depth_of(heap,act)
      bind(Heap,Next,unwound(U32.to_nat(U32.sub(d,saved)),heap,act,U32.sub(d,1),room(popped)),heap =>
        to(Return{w},popped,deepened(heap,act,saved)))
    case Stack{+act,Con{Call{+caller},rest},+top}:
      +popped : Stack = Stack{act,rest,U32.sub(top,4)}
      bind(Heap,Next,drop(heap,room(popped),act),heap => to(Return{w},with_act(popped,caller),heap))
    case Stack{+act,Con{InvokeFunction{+node},rest},+top}:
      +popped : Stack = Stack{act,rest,U32.sub(top,3)}
      choose(Result<Stop,Next>,U32.is_eq(operand(code,node,1),1),
        u => then_stack(Next,pushed(popped,InvokeArgument{node,w}),stack => to(Eval{operand(code,node,2)},stack,heap)),
        u => to(Enter{Held{w},Nil{}},popped,heap))
    case Stack{+act,Con{InvokeArgument{node,+f},rest},+top}:
      to(Enter{Held{f},[w]},Stack{act,rest,U32.sub(top,4)},heap)
    case Stack{+act,Con{Top{+phase},+rest},+top}:
      bind(Heap,Next,drop(heap,room(Stack{act,rest,top}),act),heap => topped(code,phase,w,rest,top,heap))
    case Stack{act,Nil{},top}: Fail{Internal{"no frame"}}

# §6.2: an entry is in tail position when only Scope frames separate it from
# the nearest Call or Top frame.
def tail(frames: List<&2,Frame>) -> Bool:
  match frames:
    case Con{Scope{d},rest}: tail(rest)
    case Con{Call{c},rest}: True{}
    case Con{Top{p},rest}: True{}
    case _: False{}

def unscoped_frames(frames: List<&2,Frame>, +act: U32, +top: U32) -> Stack:
  match frames:
    case Con{Scope{d},rest}: unscoped_frames(rest,act,U32.sub(top,3))
    case _: Stack{act,frames,top}

def unscoped(stack: Stack) -> Stack:
  match stack:
    case Stack{act,frames,top}: unscoped_frames(frames,act,top)

def frames_of(stack: Stack) -> List<&2,Frame>:
  match stack:
    case Stack{act,frames,top}: frames

def called(+stack: Stack, +heap: Heap) -> Result<Stop,Next>:
  choose(Result<Stop,Next>,tail(frames_of(stack)),
    u => bind(Heap,Next,drop(heap,room(unscoped(stack)),act_of(stack)),heap => to(Eval{0},with_act(unscoped(stack),0),heap)),
    u => then_stack(Next,pushed(stack,Call{act_of(stack)}),stack => to(Eval{0},with_act(stack,0),heap)))

def with_next(-B: Data, result: Result<Stop,Next>, next: Stack -> Heap -> Result<Stop,B>) -> Result<Stop,B>:
  match result:
    case Fail{stop}: Fail{stop}
    case Done{Next{control,stack,heap}}: next(stack,heap)

# Entering a body (SPEC §7): tail entries release the caller first, others
# push Call; then a fresh Activation holds the bound slots. A closure's
# captures gain references and the closure itself is dropped last.
def body_entered(+code: Code, +owner: U32, +capacity: U32, +depth: U32, +words: List<&2,U32>, +body: U32, +captures: List<&2,U32>, +closure: U32, +stack: Stack, +heap: Heap) -> Result<Stop,Next>:
  with_next(Next,called(stack,heap),+stack => heap =>
    with_cell(Next,alloc(heap,4,Con{owner,Con{depth,List.append(&2,U32,words,zeros(U32.to_nat(U32.sub(capacity,count(U32,words)))))}}),heap => a =>
      bind(Heap,Next,dups(captures,heap),heap =>
        bind(Heap,Next,drop(heap,room(stack),closure),heap => to(Eval{body},with_act(stack,a),heap)))))

def machine_of(result: Result<Stop,Next>, meter: Meter, out: List<&2,List<&2,U32>>) -> Result<Stop,Machine>:
  match result:
    case Fail{stop}: Fail{stop}
    case Done{Next{control,stack,heap}}: Done{Machine{control,stack,heap,meter,out}}

def charged(meter: Meter) -> Meter:
  match meter:
    case Meter{fuel,calls,+quantum}:
      Meter{U32.sub(fuel,1),U32.add(calls,1),Bool.pick(U32,U32.is_eq(U32.add(quantum,1),65536),0,U32.add(quantum,1))}

def fuel_of(meter: Meter) -> U32:
  match meter:
    case Meter{fuel,calls,quantum}: fuel

# §7 step 1: the target is a function, a Closure cell (the terminal
# continuation is one with node none), or an Action cell, applied to as many
# words as its arrow is live.
def admissible(+code: Code, +heap: Heap, target: Target, +ops: List<&2,U32>) -> Bool:
  match target:
    case Callee{f}: True{}
    case Held{+w}:
      +class = cell_class(heap,w)
      +node = load_word(heap,w,2)
      Bool.and(is_pointer(w),
        choose(Bool,U32.is_eq(class,3),u => U32.is_le(count(U32,ops),1),u =>
        choose(Bool,U32.is_eq(class,1),
          u => U32.is_eq(count(U32,ops),choose(U32,is_none(node),u => 1,u => operand(code,node,1))),
          u => False{})))

def is_scalar_text(codes: List<&2,U32>) -> Bool:
  match codes:
    case Nil{}: True{}
    case Con{+c,rest}: Bool.and(Bool.and(U32.is_le(c,1114111),Bool.not(within(c,55296,57343))),is_scalar_text(rest))

# Applying an Action to its continuation performs its one effect. Only
# IO.print is modelled here; other foreign leaves are refused, never faked.
def performed(+code: Code, +w: U32, +k: U32, +stack: Stack, +heap: Heap, meter: Meter, out: List<&2,List<&2,U32>>) -> Result<Stop,Machine>:
  choose(Result<Stop,Machine>,Bool.not(U32.is_eq(load_word(heap,w,2),1)),
    u => Fail{Unsupported{"vm",String.append("foreign ",U32.show(load_word(heap,w,2)))}},
    u => bind(List<&2,U32>,Machine,string_of(code,heap,load_word(heap,w,3)),+line =>
      choose(Result<Stop,Machine>,Bool.not(is_scalar_text(scalars_of(line,heap))),u => Fail{Refused{"io","abi"}},u =>
        bind(Heap,Machine,drop(heap,room(stack),w),heap2 =>
          Done{Machine{Enter{Held{k},[immediate(0)]},stack,heap2,meter,Con{scalars_of(line,heap),out}}}))))

def held_entered(+code: Code, +w: U32, +ops: List<&2,U32>, +stack: Stack, +heap: Heap, +meter: Meter, +out: List<&2,List<&2,U32>>) -> Result<Stop,Machine>:
  +node = load_word(heap,w,2)
  +captures = slice(U32.to_nat(U32.sub(U32.shrn(load_word(heap,w,1),3n),1)),memory_of(heap),U32.add(U32.shrn(w,2n),3))
  choose(Result<Stop,Machine>,U32.is_eq(cell_class(heap,w),3),
    u => choose(Result<Stop,Machine>,U32.is_eq(count(U32,ops),0),
      u => Done{Machine{Return{w},stack,heap,meter,out}},
      u => performed(code,w,nth(ops,0),stack,heap,meter,out)),
    u => choose(Result<Stop,Machine>,is_none(node),
      u => machine_of(with_cell(Next,alloc(heap,0,[rep(code,10),0,nth(ops,0)]),heap => e => to(Return{e},stack,heap)),meter,out),
      u => machine_of(body_entered(code,node,operand(code,node,2),U32.add(count(U32,captures),count(U32,ops)),
             List.append(&2,U32,captures,ops),node_last(code,node),captures,w,stack,heap),meter,out)))

def target_entered(+code: Code, target: Target, +ops: List<&2,U32>, +stack: Stack, +heap: Heap, meter: Meter, out: List<&2,List<&2,U32>>) -> Result<Stop,Machine>:
  match target:
    case Callee{+f}:
      +record = function_record(code,f)
      +body = code_word(code,U32.add(record,5))
      machine_of(body_entered(code,body,code_word(code,U32.add(record,4)),code_word(code,U32.add(record,3)),ops,body,Nil{},0,stack,heap),meter,out)
    case Held{+w}: held_entered(code,w,ops,stack,heap,meter,out)

# Enter (SPEC §7): check the target, pay one fuel, then run the target.
def entered(+code: Code, +target: Target, +ops: List<&2,U32>, +stack: Stack, +heap: Heap, +meter: Meter, out: List<&2,List<&2,U32>>) -> Result<Stop,Machine>:
  choose(Result<Stop,Machine>,Bool.not(admissible(code,heap,target,ops)),u => ill_typed(Machine),u =>
  choose(Result<Stop,Machine>,U32.is_eq(fuel_of(meter),0),u => Fail{Exhausted{1,"fuel"}},u =>
    target_entered(code,target,ops,stack,heap,charged(meter),out)))

def step(+code: Code, m: Machine) -> Result<Stop,Machine>:
  match m:
    case Machine{Eval{+node},stack,heap,meter,out}: machine_of(evaluated(node_op(code,node),code,node,stack,heap),meter,out)
    case Machine{Return{w},stack,heap,meter,out}: machine_of(returned(code,w,stack,heap),meter,out)
    case Machine{Enter{target,ops},stack,heap,meter,out}: entered(code,target,ops,stack,heap,meter,out)
    case Machine{Finished{outcome},stack,heap,meter,out}: Done{Machine{Finished{outcome},stack,heap,meter,out}}

def halted(m: Machine, stop: Stop) -> Machine:
  match m:
    case Machine{control,stack,heap,meter,out}: Machine{Finished{Stopped{stop,control}},stack,heap,meter,out}

# A refused step leaves the machine as it was and records why.
def settled(result: Result<Stop,Machine>, m: Machine) -> Machine:
  match result:
    case Fail{stop}: halted(m,stop)
    case Done{next}: next

def is_finished(m: Machine) -> Bool:
  match m:
    case Machine{Finished{o},stack,heap,meter,out}: True{}
    case _: False{}

# Transitions until the machine finishes. The Nat bound is the model's own
# harness limit, reported as `Bound`, never as VM exhaustion.
def run(fuel: Nat, +code: Code, +m: Machine) -> Machine:
  match fuel:
    case 0n: halted(m,Bound{"transitions"})
    case 1n+f: choose(Machine,is_finished(m),u => m,u => run(f,code,settled(step(code,m),m)))

# ---------------------------------------------------------------- describing a Book result

type Piece is Data:
  Shown{word: U32, result: U32}
  Said{text: List<&2,U32>}

def text(s: String) -> List<&2,U32>:
  match s:
    case SNil{}: Nil{}
    case SCon{Chr{c},rest}: Con{c,text(rest)}

def repeated_text(n: Nat, +t: List<&2,U32>) -> List<&2,U32>:
  match n:
    case 0n: Nil{}
    case 1n+m: List.append(&2,U32,t,repeated_text(m,t))

def image_of_code(code: Code) -> Store:
  match code:
    case Code{image,types,constructors,functions,names,pool,reps,terminal}: image

def name_codes(+code: Code, +n: U32) -> List<&2,U32>:
  +record = name_record(code,n)
  Maybe.default(&2,List<&2,U32>,scalars(List.take(&2,U32,unpack(slice(U32.to_nat(U32.sub(code_word(code,record),2)),image_of_code(code),U32.add(record,2))),U32.to_nat(code_word(code,U32.add(record,1))))),Nil{})

def field_pieces(n: Nat, +code: Code, +heap: Heap, +t: U32, +tag: U32, +w: U32, +i: U32) -> List<&2,Piece>:
  match n:
    case 0n: [Said{text("}")}]
    case 1n+m:
      Con{Said{Bool.pick(List<&2,U32>,U32.is_eq(i,0),Nil{},text(","))},Con{Shown{load_word(heap,w,U32.add(4,i)),field_type(code,t,tag,i)},
        field_pieces(m,code,heap,t,tag,w,U32.add(i,1))}}

def pieces(+code: Code, +heap: Heap, +w: U32, +t: U32) -> List<&2,Piece>:
  +tag = tag_of(code,heap,t,w)
  +name = name_codes(code,code_word(code,U32.add(constructor_record(code,t,tag),3)))
  +fields = field_count(code,t,tag)
  choose(List<&2,Piece>,is_rep(code,t,0),
    u => [Said{List.append(&2,U32,repeated_text(U32.to_nat(scalar(heap,w)),text("Succ{")),List.append(&2,U32,text("Zero{}"),repeated_text(U32.to_nat(scalar(heap,w)),text("}"))))}],
    u => choose(List<&2,Piece>,U32.is_eq(fields,0),u => [Said{List.append(&2,U32,name,text("{}"))}],
      u => Con{Said{List.append(&2,U32,name,text("{"))},field_pieces(U32.to_nat(fields),code,heap,t,tag,w,0)}))

def display_limit() -> U32:
  16777216

def visit_limit() -> U32:
  1048576

# §8: an iterative walk bounded by 1,048,576 visits and 16 MiB of text; a
# Nat's unary spelling is sized before it is spelled.
def render(fuel: Nat, +code: Code, +heap: Heap, work: List<&2,Piece>, +visits: U32, +size: U32, parts: List<&2,List<&2,U32>>) -> Result<Stop,List<&2,U32>>:
  match fuel work:
    case _ Nil{}: Done{List.concat(&2,U32,List.reverse(&2,List<&2,U32>,parts))}
    case 0n _: Fail{Internal{"render fuel"}}
    case 1n+ +f Con{Said{+t},rest}:
      choose(Result<Stop,List<&2,U32>>,U32.is_gt(count(U32,t),U32.sub(display_limit(),size)),u => Fail{Exhausted{2,"display"}},u =>
        render(f,code,heap,rest,visits,U32.add(size,count(U32,t)),Con{t,parts}))
    case 1n+ +f Con{Shown{+w,+t},rest}:
      choose(Result<Stop,List<&2,U32>>,U32.is_ge(visits,visit_limit()),u => Fail{Exhausted{2,"display"}},u =>
      inspected_at(List<&2,U32>,code,heap,t,w,u =>
      choose(Result<Stop,List<&2,U32>>,Bool.and(is_rep(code,t,0),U32.is_gt(scalar(heap,w),U32.div(U32.sub(display_limit(),size),6))),u => Fail{Exhausted{2,"display"}},u =>
        render(f,code,heap,List.append(&2,Piece,pieces(code,heap,w,t),rest),U32.add(visits,1),size,parts))))

def described(+code: Code, +heap: Heap, +w: U32, +t: U32) -> Result<Stop,List<&2,U32>>:
  render(U32.to_nat(none()),code,heap,[Shown{w,t}],0,0,Nil{})

# ---------------------------------------------------------------- booting

def indexed(offsets: List<&2,U32>, store: Store, +i: U32) -> Store:
  match offsets:
    case Nil{}: store
    case Con{a,rest}: indexed(rest,write(store,i,a),U32.add(i,1))

type Pooled is Data:
  Pooled{heap: Heap, pool: Store}

def with_pooled(-B: Data, result: Result<Stop,Pooled>, next: Heap -> Store -> Result<Stop,B>) -> Result<Stop,B>:
  match result:
    case Fail{stop}: Fail{stop}
    case Done{Pooled{heap,pool}}: next(heap,pool)

def immortal_scalar(+heap: Heap, +v: U32) -> Result<Stop,Cell>:
  choose(Result<Stop,Cell>,boxed(v),u => allocate(heap,none(),2,[v]),u => Done{Cell{heap,immediate(v)}})

# A String constant is an immortal SCon chain built from its last character,
# each boxed code in a Big cell just before the SCon holding it (SPEC §5).
def immortal_chain(last_first: List<&2,U32>, +string: U32, +heap: Heap, +tail: U32) -> Result<Stop,Cell>:
  match last_first:
    case Nil{}: Done{Cell{heap,tail}}
    case Con{c,rest}:
      with_cell(Cell,immortal_scalar(heap,c),heap => char =>
        with_cell(Cell,allocate(heap,none(),0,[string,1,char,tail]),heap => w => immortal_chain(rest,string,heap,w)))

def pooled(constants: List<&2,U32>, +image: Store, +string: U32, +heap: Heap, +pool: Store, +i: U32) -> Result<Stop,Pooled>:
  match constants:
    case Nil{}: Done{Pooled{heap,pool}}
    case Con{+a,rest}:
      with_cell(Pooled,choose(Result<Stop,Cell>,U32.is_eq(read(image,U32.add(a,1)),3),
          u => immortal_chain(List.reverse(&2,U32,slice(U32.to_nat(read(image,U32.add(a,2))),image,U32.add(a,3))),string,heap,immediate(0)),
          u => immortal_scalar(heap,read(image,U32.add(a,3)))),heap => w =>
        pooled(rest,image,string,heap,write(pool,i,w),U32.add(i,1)))

type Booted is Data:
  Booted{code: Code, heap: Heap}

def terminal_cell(+program: Bool, +heap: Heap) -> Result<Stop,Cell>:
  choose(Result<Stop,Cell>,program,u => allocate(heap,none(),1,[none()]),u => Done{Cell{heap,0}})

# Load time (SPEC §5): constants materialize in index order from the heap
# base, immortal; a Program then gets its immortal terminal continuation.
def booted_sections(lists: List<&2,List<&2,U32>>, +image: Store, +total: U32) -> Result<Stop,Booted>:
  match lists:
    case Con{t,Con{c,Con{f,Con{k,Con{n,Con{m,Nil{}}}}}}}:
      +reps = slice(12n,image,12)
      with_pooled(Booted,pooled(k,image,nth(reps,3),Heap{empty(),heap_base(total),zeros(29n)},empty(),0),heap => pool =>
        with_cell(Booted,terminal_cell(U32.is_eq(read(image,3),1),heap),heap => last =>
          Done{Booted{Code{image,indexed(t,empty(),0),indexed(c,empty(),0),indexed(f,empty(),0),indexed(m,empty(),0),pool,reps,last},heap}}))
    case _: Fail{Internal{"sections"}}

def boot(+words: List<&2,U32>) -> Result<Stop,Booted>:
  +image = stored(words,empty(),0)
  +total = count(U32,words)
  bind(List<&2,List<&2,U32>>,Booted,refused(List<&2,List<&2,U32>>,sections(List<&2,List<&2,U32>>,6n,image,total,0,32,Nil{},lists => Done{lists})),lists =>
    booted_sections(lists,image,total))

# ---------------------------------------------------------------- Books and Programs

def constructor_fields(cs: List<&2,Constructor>) -> List<&2,List<&2,U32>>:
  match cs:
    case Nil{}: Nil{}
    case Con{Constructor{name,fields},rest}: Con{fields,constructor_fields(rest)}

# §8's describe domain: algebraic, with every live field of every constructor
# describable in turn; a cycle through algebraic types stays describable.
def describable(fuel: Nat, +types: List<&2,Sort>, work: List<&2,U32>, +seen: List<&2,U32>) -> Bool:
  match fuel work:
    case _ Nil{}: True{}
    case 0n _: False{}
    case 1n+ +f Con{+t,+rest}:
      choose(Bool,is_none(t),u => False{},u =>
      choose(Bool,member(seen,t),u => describable(f,types,rest,seen),u =>
      choose(Bool,Bool.not(U32.is_eq(kind(types,t),0)),u => False{},u =>
        describable(f,types,List.append(&2,U32,List.concat(&2,U32,constructor_fields(constructors_of(types,t))),rest),Con{t,seen}))))

# Host ordinals are nullary tags of the parameter types, checked in
# parameter order as eval-cli checks them.
def arguments(parameters: List<&2,U32>, ordinals: List<&2,U32>, +types: List<&2,Sort>) -> Result<Stop,List<&2,U32>>:
  match parameters ordinals:
    case Nil{} Nil{}: Done{Nil{}}
    case Con{+p,ps} Con{+o,os}:
      choose(Result<Stop,List<&2,U32>>,Bool.not(U32.is_eq(kind(types,p),0)),u => Fail{Refused{"invoke","structured-argument"}},u =>
      choose(Result<Stop,List<&2,U32>>,U32.is_ge(o,count(Constructor,constructors_of(types,p))),u => Fail{Refused{"invoke","argument-range"}},u =>
      choose(Result<Stop,List<&2,U32>>,Bool.not(U32.is_eq(count(U32,fields_of(constructors_of(types,p),o)),0)),u => Fail{Refused{"invoke","structured-argument"}},u =>
        bind(List<&2,U32>,List<&2,U32>,arguments(ps,os,types),words => Done{Con{immediate(o),words}}))))
    case _ _: Fail{Refused{"invoke","argument-arity"}}

def with_function(-B: Data, found: Maybe<&2,Function>, next: List<&2,U32> -> U32 -> Result<Stop,B>) -> Result<Stop,B>:
  match found:
    case None{}: Fail{Refused{"invoke","unknown-export"}}
    case Some{Function{name,parameters,result,slots,body}}: next(parameters,result)

# A Book request (SPEC §8) reads only the image: the export, its arguments and
# its describable result, before any fuel is spent.
def book(+plan: Plan, +booted: Booted, +name: List<&2,U32>, +fuel: U32, ordinals: List<&2,U32>) -> Result<Stop,Machine>:
  match plan booted:
    case Plan{entry,+types,+functions,reps} Booted{code,heap}:
      +index = function_index(functions,name,0)
      with_function(Machine,function_at(functions,index),parameters => +result =>
        bind(List<&2,U32>,Machine,arguments(parameters,ordinals,types),words =>
          choose(Result<Stop,Machine>,Bool.not(describable(U32.to_nat(none()),types,[result],Nil{})),u => Fail{Unsupported{"invoke","result-type"}},u =>
            Done{Machine{Enter{Callee{index},words},Stack{0,[Top{0}],3},heap,Meter{fuel,0,0},Nil{}}})))

def program(+plan: Plan, +booted: Booted, +fuel: U32) -> Machine:
  match plan booted:
    case Plan{entry,types,+functions,reps} Booted{code,heap}:
      Machine{Enter{Callee{function_index(functions,main_bytes(),0)},Nil{}},Stack{0,[Top{1}],3},heap,Meter{fuel,0,0},Nil{}}

def code_of(booted: Booted) -> Code:
  match booted:
    case Booted{code,heap}: code

def result_type(+plan: Plan, +name: List<&2,U32>) -> U32:
  match plan:
    case Plan{entry,types,functions,reps}: callee_result(function_at(functions,function_index(functions,name,0)))

# A Book's answer is described, then dropped (SPEC §8).
def concluded(+code: Code, +t: U32, m: Machine) -> Result<Stop,Machine>:
  match m:
    case Machine{Finished{Answered{+w}},+stack,+heap,+meter,+out}:
      bind(List<&2,U32>,Machine,described(code,heap,w,t),tree =>
        bind(Heap,Machine,drop(heap,room(stack),w),heap2 =>
          Done{Machine{Finished{Described{t,tag_of(code,heap,t,w),tree}},stack,heap2,meter,out}}))
    case _: Done{m}

# ---------------------------------------------------------------- the RC audit

def chase(fuel: Nat, +heap: Heap, +p: U32, +marks: Store) -> Store:
  match fuel:
    case 0n: marks
    case 1n+f: choose(Store,U32.is_eq(p,0),u => marks,u => chase(f,heap,load_word(heap,p,0),write(marks,U32.shrn(p,2n),1)))

def free_marks(heads: List<&2,U32>, +heap: Heap, marks: Store) -> Store:
  match heads:
    case Nil{}: marks
    case Con{p,rest}: free_marks(rest,heap,chase(U32.to_nat(memory_words()),heap,p,marks))

def bump_of(heap: Heap) -> U32:
  match heap:
    case Heap{memory,bump,free}: bump

def free_of(heap: Heap) -> List<&2,U32>:
  match heap:
    case Heap{memory,bump,free}: free

# Cells from `q` to the bump pointer, skipping free cells; a block size below
# four words means the heap is corrupt and ends the walk.
def blocks(fuel: Nat, +heap: Heap, +marks: Store, +q: U32, +bump: U32, +found: List<&2,U32>) -> List<&2,U32>:
  match fuel:
    case 0n: found
    case 1n+f:
      +memory = memory_of(heap)
      +size = choose(U32,U32.is_eq(read(marks,q),1),u => read(memory,U32.add(q,1)),
        u => U32.shln(4,U32.to_nat(class_of(U32.add(2,U32.shrn(read(memory,U32.add(q,1)),3n))))))
      choose(List<&2,U32>,Bool.or(U32.is_ge(q,bump),U32.is_lt(size,4)),u => found,u =>
        blocks(f,heap,marks,U32.add(q,size),bump,Bool.pick(List<&2,U32>,U32.is_eq(read(marks,q),1),found,Con{U32.shln(q,2n),found})))

def live_cells(+heap: Heap, +base: U32) -> List<&2,U32>:
  blocks(U32.to_nat(memory_words()),heap,free_marks(free_of(heap),heap,empty()),base,bump_of(heap),Nil{})

def mortal_cells(cells: List<&2,U32>, +heap: Heap) -> List<&2,U32>:
  match cells:
    case Nil{}: Nil{}
    case Con{+c,+rest}: choose(List<&2,U32>,mortal(heap,c),u => Con{c,mortal_cells(rest,heap)},u => mortal_cells(rest,heap))

def all_edges(cells: List<&2,U32>, +heap: Heap) -> List<&2,U32>:
  match cells:
    case Nil{}: Nil{}
    case Con{c,rest}: List.append(&2,U32,edges(heap,c),all_edges(rest,heap))

def frame_roots(frames: List<&2,Frame>) -> List<&2,U32>:
  match frames:
    case Nil{}: Nil{}
    case Con{Gather{node,need,got},rest}: List.append(&2,U32,got,frame_roots(rest))
    case Con{Call{caller},rest}: Con{caller,frame_roots(rest)}
    case Con{InvokeArgument{node,f},rest}: Con{f,frame_roots(rest)}
    case Con{frame,rest}: frame_roots(rest)

def control_roots(control: Control) -> List<&2,U32>:
  match control:
    case Return{w}: [w]
    case Enter{Held{w},ops}: Con{w,ops}
    case Enter{Callee{f},ops}: ops
    case Finished{Answered{w}}: [w]
    case Finished{Stopped{stop,pending}}: control_roots(pending)
    case _: Nil{}

# Every owner of a reference: the result register, pending operands, the
# current Activation and every frame value (SPEC §6).
def roots(m: Machine) -> List<&2,U32>:
  match m:
    case Machine{control,Stack{act,frames,top},heap,meter,out}: Con{act,List.append(&2,U32,control_roots(control),frame_roots(frames))}

def tallied(words: List<&2,U32>, +heap: Heap, +counts: Store) -> Store:
  match words:
    case Nil{}: counts
    case Con{+w,rest}:
      tallied(rest,heap,choose(Store,mortal(heap,w),u => write(counts,U32.shrn(w,2n),U32.add(read(counts,U32.shrn(w,2n)),1)),u => counts))

def mortal_words(words: List<&2,U32>, +heap: Heap) -> U32:
  match words:
    case Nil{}: 0
    case Con{+w,rest}: U32.add(Bool.pick(U32,mortal(heap,w),1,0),mortal_words(rest,heap))

def matched(cells: List<&2,U32>, +heap: Heap, +counts: Store) -> Bool:
  match cells:
    case Nil{}: True{}
    case Con{+c,rest}: Bool.and(U32.is_eq(rc_of(heap,c),read(counts,U32.shrn(c,2n))),matched(rest,heap,counts))

def counted_total(cells: List<&2,U32>, +counts: Store) -> U32:
  match cells:
    case Nil{}: 0
    case Con{+c,rest}: U32.add(read(counts,U32.shrn(c,2n)),counted_total(rest,counts))

def heap_of(m: Machine) -> Heap:
  match m:
    case Machine{control,stack,heap,meter,out}: heap

def base_of(+code: Code) -> U32:
  heap_base(code_word(code,2))

# An Activation's slots at and above its depth hold 0 (SPEC §5).
def vacant(cells: List<&2,U32>, +heap: Heap) -> Bool:
  match cells:
    case Nil{}: True{}
    case Con{+c,rest}:
      +depth = load_word(heap,c,3)
      +capacity = U32.sub(U32.shrn(load_word(heap,c,1),3n),2)
      Bool.and(choose(Bool,Bool.or(Bool.not(U32.is_eq(cell_class(heap,c),4)),U32.is_gt(depth,capacity)),u => True{},
          u => zero_all(slice(U32.to_nat(U32.sub(capacity,depth)),memory_of(heap),U32.add(U32.shrn(c,2n),U32.add(4,depth))))),
        vacant(rest,heap))

# The RC audit: each live mortal cell's count equals its owners among the
# roots and every live cell's edges, no owner points outside them, and no
# Activation holds a word above its depth.
def balanced(+code: Code, +m: Machine) -> Bool:
  +heap = heap_of(m)
  +cells = live_cells(heap,base_of(code))
  +owners = List.append(&2,U32,roots(m),all_edges(cells,heap))
  +counts = tallied(owners,heap,empty())
  +mortals = mortal_cells(cells,heap)
  Bool.and(Bool.and(matched(mortals,heap,counts),U32.is_eq(counted_total(mortals,counts),mortal_words(owners,heap))),vacant(cells,heap))

# Mortal cells still live; zero once a finished run has released its answer.
def leaked(+code: Code, +m: Machine) -> U32:
  count(U32,mortal_cells(live_cells(heap_of(m),base_of(code)),heap_of(m)))

type Audit is Data:
  Audit{machine: Machine, steps: U32, balanced: Bool}

# Runs like `run`, auditing before every transition and after the last.
def audited(fuel: Nat, +code: Code, +m: Machine, +steps: U32) -> Audit:
  match fuel:
    case 0n: Audit{halted(m,Bound{"transitions"}),steps,balanced(code,m)}
    case 1n+f:
      choose(Audit,Bool.not(balanced(code,m)),u => Audit{m,steps,False{}},u =>
      choose(Audit,is_finished(m),u => Audit{m,steps,True{}},u =>
        audited(f,code,settled(step(code,m),m),U32.add(steps,1))))

# ---------------------------------------------------------------- law predicates

# An admitted image's entry run to its end: a Book's `main` with no ordinals,
# described and dropped, or a Program's `main`. `Bound` stops a run that
# outlives the transition budget.
type Run is Data:
  Refusal{stop: Stop}
  Ran{code: Code, machine: Machine, balanced: Bool}

def plan_entry(plan: Plan) -> U32:
  match plan:
    case Plan{entry,types,functions,reps}: entry

# The answer's description and drop are audited too.
def concluded_run(+code: Code, result: Result<Stop,Machine>, ok: Bool) -> Run:
  match result:
    case Fail{stop}: Refusal{stop}
    case Done{+m}: Ran{code,m,Bool.and(ok,balanced(code,m))}

def run_concluded(+code: Code, +t: U32, a: Audit) -> Run:
  match a:
    case Audit{m,steps,ok}: concluded_run(code,concluded(code,t,m),ok)

def started_run(+code: Code, +t: U32, +steps: Nat, result: Result<Stop,Machine>) -> Run:
  match result:
    case Fail{stop}: Refusal{stop}
    case Done{m}: run_concluded(code,t,audited(steps,code,m,0))

def ran(+plan: Plan, +steps: Nat, +fuel: U32, booted: Result<Stop,Booted>) -> Run:
  match booted:
    case Fail{stop}: Refusal{stop}
    case Done{+b}:
      +code = code_of(b)
      choose(Run,U32.is_eq(plan_entry(plan),1),
        u => run_concluded(code,none(),audited(steps,code,program(plan,b,fuel),0)),
        u => started_run(code,result_type(plan,main_bytes()),steps,book(plan,b,main_bytes(),fuel,Nil{})))

def admitted_run(result: Result<Stop,Plan>, +words: List<&2,U32>, +steps: Nat, +fuel: U32) -> Run:
  match result:
    case Fail{stop}: Refusal{stop}
    case Done{+plan}: ran(plan,steps,fuel,boot(words))

def run_words(+words: List<&2,U32>, +steps: Nat, +fuel: U32) -> Run:
  admitted_run(admit(words),words,steps,fuel)

def internal(outcome: Outcome) -> Bool:
  match outcome:
    case Stopped{Internal{c},p}: True{}
    case Stopped{Bound{c},p}: True{}
    case _: False{}

def finished_outcome(m: Machine) -> Outcome:
  match m:
    case Machine{Finished{o},stack,heap,meter,out}: o
    case _: Stopped{Internal{"unfinished"},Eval{0}}

def completing(outcome: Outcome) -> Bool:
  match outcome:
    case Described{t,tag,tree}: True{}
    case Emitted{}: True{}
    case Died{c,msg}: True{}
    case _: False{}

# Validator soundness: an image is refused, or its run never meets a state the
# machine's invariants exclude, keeps every count balanced and, when it
# completes, leaves no mortal cell live.
def sound(run: Run) -> Bool:
  match run:
    case Refusal{stop}: Bool.not(internal(Stopped{stop,Eval{0}}))
    case Ran{+code,+m,balanced}:
      Bool.and(Bool.and(Bool.not(internal(finished_outcome(m))),balanced),
        Bool.or(Bool.not(completing(finished_outcome(m))),U32.is_eq(leaked(code,m),0)))

def balanced_run(run: Run) -> Bool:
  match run:
    case Refusal{stop}: False{}
    case Ran{code,m,balanced}: balanced

def leak_of(run: Run) -> U32:
  match run:
    case Refusal{stop}: none()
    case Ran{+code,+m,balanced}: leaked(code,m)

def outcome_of(run: Run) -> Outcome:
  match run:
    case Refusal{stop}: Stopped{stop,Eval{0}}
    case Ran{code,m,balanced}: finished_outcome(m)

# Single-word mutations of an image: at each position, zero and the successor
# and predecessor of the word there (so none where the word is zero).
def mutations(n: Nat, +words: List<&2,U32>, +i: U32) -> List<&2,List<&2,U32>>:
  match n:
    case 0n: Nil{}
    case 1n+m:
      +w = nth(words,i)
      Con{replaced(words,i,0),Con{replaced(words,i,U32.add(w,1)),Con{replaced(words,i,U32.sub(w,1)),mutations(m,words,U32.add(i,1))}}}

def all_sound(images: List<&2,List<&2,U32>>, +steps: Nat, +fuel: U32) -> Bool:
  match images:
    case Nil{}: True{}
    case Con{+w,rest}: Bool.and(sound(run_words(w,steps,fuel)),all_sound(rest,steps,fuel))

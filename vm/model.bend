import Base

# The normative model of knot-image-1 and knot-vm-1 (vm/SPEC.md).
# Words are u32; `none` is 0xffffffff. A reason is the refusal text of SPEC §4,
# spelled as vm/serializer.py spells its first problem.

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
def records(n: Nat, +image: Store, +total: U32, +section: U32, +at: U32, found: List<&2,U32>, next: List<&2,U32> -> U32 -> Result<String,Plan>) -> Result<String,Plan>:
  match n:
    case 0n: next(List.reverse(&2,U32,found),at)
    case 1n+m:
      +size = read(image,at)
      unless(Plan,Bool.or(U32.is_ge(at,total),Bool.or(U32.is_lt(size,2),U32.is_gt(size,U32.sub(total,at)))),
        String.concat(["section ",U32.show(section)," record length"]),u =>
        records(m,image,total,section,U32.add(at,size),Con{at,found},next))

def sections(n: Nat, +image: Store, +total: U32, +section: U32, +cursor: U32, found: List<&2,List<&2,U32>>, next: List<&2,List<&2,U32>> -> Result<String,Plan>) -> Result<String,Plan>:
  match n:
    case 0n: unless(Plan,Bool.not(U32.is_eq(cursor,total)),"trailing words",u => next(List.reverse(&2,List<&2,U32>,found)))
    case 1n+m:
      +count = read(image,cursor)
      unless(Plan,Bool.not(U32.is_eq(read(image,U32.add(5,section)),cursor)),String.concat(["section ",U32.show(section)," offset"]),u =>
      unless(Plan,U32.is_gt(count,1048576),"record count",u =>
      records(U32.to_nat(count),image,total,section,U32.add(cursor,1),Nil{},list => end =>
        sections(m,image,total,U32.add(section,1),end,Con{list,found},next))))


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

def operand(role: Role) -> Bool:
  match role:
    case Operand{}: True{}
    case _: False{}

def inspected(+env: Env, +at: U32, role: Role) -> Result<String,Unit>:
  match env:
    case Env{+image,starts,+types,+constants}:
      +t = read(image,U32.add(at,2))
      +op = read(image,U32.add(at,1))
      unless(Unit,Bool.and(Bool.not(is_none(t)),U32.is_ge(t,types)),"type index",u =>
      unless(Unit,Bool.and(is_arm(op),operand(role)),"standalone arm",u =>
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

# Children in SPEC §3 order; an absent row or default has no record.
def children(op: Nat, +image: Store, +x: U32, +last: U32, +listed: List<&2,U32>) -> List<&2,Job>:
  match op:
    case 1n: operands(listed)
    case 2n: operands([read(image,x)])
    case 4n: operands(listed)
    case 6n: operands(listed)
    case 7n: operands([read(image,U32.add(x,1)),read(image,U32.add(x,2))])
    case 8n:
      +n = read(image,U32.add(x,3))
      List.append(&2,Job,choose(List<&2,Job>,U32.is_eq(read(image,U32.add(x,2)),0),
        u => tag_rows(slice(U32.to_nat(n),image,U32.add(x,4))),
        u => key_rows(U32.to_nat(n),image,U32.add(x,4))),fallback(last))
    case 9n: operands([read(image,U32.add(x,3))])
    case 10n: operands([last])
    case 11n: Con{Job{read(image,x),Operand{}},operands(listed)}
    case 12n: operands(listed)
    case _: Nil{}

def kids(+image: Store, +at: U32) -> List<&2,Job>:
  +x = U32.add(at,3)
  children(U32.to_nat(read(image,U32.add(at,1))),image,x,read(image,U32.sub(U32.add(at,read(image,at)),1)),
    slice(U32.to_nat(read(image,U32.add(x,1))),image,U32.add(x,2)))

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
    sections(6n,image,total,0,32,Nil{},lists => decoded(lists,image,total))))))

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

# registry.json ids 0..38 in order; 39 and 40 are reserved and absent.
def prims() -> List<&2,Primitive>:
  +w2 : List<&2,U32> = [1,1]
  +n2 : List<&2,U32> = [0,0]
  [Primitive{w2,1},Primitive{w2,1},Primitive{w2,1},Primitive{w2,1},Primitive{w2,1},Primitive{[1],1},Primitive{w2,1},
   Primitive{w2,5},Primitive{w2,4},Primitive{w2,4},Primitive{w2,4},Primitive{w2,4},Primitive{w2,4},Primitive{w2,4},
   Primitive{[1,0],1},Primitive{[1,0],1},Primitive{[1],0},Primitive{[0],1},Primitive{[1],2},Primitive{[2],1},
   Primitive{[2,2],4},Primitive{[2],4},
   Primitive{n2,0},Primitive{n2,0},Primitive{n2,0},Primitive{n2,5},
   Primitive{n2,4},Primitive{n2,4},Primitive{n2,4},Primitive{n2,4},Primitive{n2,4},Primitive{n2,4},
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

def representation_at(+reps: List<&2,U32>, +r: U32) -> U32:
  nth(reps,r)

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

def arm_body(node: Maybe<&2,Node>) -> List<&2,Node>:
  match node:
    case Some{Branch{key,first,fields,body}}: [body]
    case Some{Default{body}}: [body]
    case _: Nil{}

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

def functions_of(cx: Context) -> List<&2,Function>:
  match cx:
    case Context{types,functions,reps}: functions

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
def program(+entry: U32, +cx: Context) -> Result<String,Unit>:
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
      then(Unit,Unit,program(entry,cx),u => functions_valid(functions,cx)))))

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

def big(+n: Nat) -> Nat:
  Nat.add(n,U32.to_nat(4294967295))

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

# SPEC §4: size first, then the bytes, the plan's rules and canonicality. The
# loader never runs a body.
def load(+bytes: List<&2,U32>) -> Result<Stop,Plan>:
  +size = count(U32,bytes)
  choose(Result<Stop,Plan>,U32.is_gt(size,image_limit()),u => Fail{Exhausted{2,"image-size"}},u =>
  choose(Result<Stop,Plan>,Bool.or(Bool.not(U32.is_eq(U32.mod(size,4),0)),U32.is_lt(size,128)),u => Fail{Refused{"image","length"}},u =>
    refused(Plan,then(Plan,Plan,decode(pack(bytes)),+plan => admitted(pack(bytes),plan)))))

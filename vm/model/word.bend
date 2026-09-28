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

def slice(n: Nat, +image: Store, +from: U32) -> List<&2,U32>:
  match n:
    case 0n: Nil{}
    case 1n+m: Con{read(image,from),slice(m,image,U32.add(from,1))}

def zero_all(bytes: List<&2,U32>) -> Bool:
  match bytes:
    case Nil{}: True{}
    case Con{b,rest}: Bool.and(U32.is_eq(b,0),zero_all(rest))

def nth_bool(xs: List<&2,Bool>, +i: U32) -> Bool:
  match xs:
    case Nil{}: False{}
    case Con{+x,+rest}: choose(Bool,U32.is_eq(i,0),u => x,u => nth_bool(rest,U32.sub(i,1)))

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


# ---------------------------------------------------------------- stops

# How the machine stops short of an answer (SPEC §11). `Exhausted` keeps its
# host kind and precise cause; `Bound` is the model's own transition bound,
# a harness limit that never excuses the VM.
type Stop is Data:
  Exhausted{kind: U32, cause: String}
  Refused{phase: String, code: String}
  Unsupported{phase: String, code: String}
  Internal{code: String}
  Bound{code: String}

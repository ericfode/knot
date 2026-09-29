import Base
import ./syntax.bend as S

# knot-image-1 (vm/SPEC.md): the image plan and the words every part of the codec shares.
# A checked Book is erased to a Plan (image.bend), a Plan is laid out as words (image-layout.bend), and
# image-decode.bend inverts the layout.

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

def exhausted(-A: Type) -> Result<S.Error,A>:
  Fail{S.Exhausted{"compile",S.At{0,0,0,0}}}

def same_words(xs: List<&2,U32>, ys: List<&2,U32>) -> Bool:
  match xs ys:
    case Nil{} Nil{}: True{}
    case Con{+a,at} Con{+b,bt}: Bool.and(U32.is_eq(a,b),same_words(at,bt))
    case _ _: False{}

def main_index(functions: List<&2,Function>, +index: U32) -> U32:
  match functions:
    case Nil{}: none()
    case Con{Function{+name,parameters,result,slots,body},+tail}:
      S.choose(U32,String.eq(name,"main"),u => index,u => main_index(tail,U32.add(index,1)))

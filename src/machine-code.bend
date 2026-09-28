import Base
import ./syntax.bend as S

# Runtime fragments use the Wasm binary opcodes. Indices below 128 have their
# one-byte LEB spelling; constants and section lengths use these total codecs.
def length_from(xs: List<&2,U32>, count: U32) -> U32:
  match xs:
    case Nil{}: count
    case Con{head,tail}: length_from(tail,U32.add(count,1))

def length(xs: List<&2,U32>) -> U32:
  length_from(xs,0)

def join(parts: List<&2,List<&2,U32>>, reversed: List<&2,U32>) -> List<&2,U32>:
  match parts:
    case Nil{}: List.reverse(&2,U32,reversed)
    case Con{head,tail}: join(tail,List.reverse.go(&2,U32,head,reversed))

def seq(parts: List<&2,List<&2,U32>>) -> List<&2,U32>:
  join(parts,Nil{})

def groups(fuel: Nat, +limit: U32, +value: U32) -> List<&2,U32>:
  match fuel:
    case 0n: [value]
    case 1n+n:
      S.choose(List<&2,U32>,U32.is_lt(value,limit),u => [value],u =>
        Con{U32.add(U32.and(value,127),128),groups(n,limit,U32.shrn(value,7n))})

def unsigned(value: U32) -> List<&2,U32>:
  groups(4n,128,value)

def signed_positive(value: U32) -> List<&2,U32>:
  groups(4n,64,value)

def signed(+value: U32) -> List<&2,U32>:
  S.choose(List<&2,U32>,U32.is_lt(value,2147483648),u => signed_positive(value),u =>
    [U32.or(U32.and(value,127),128),U32.or(U32.and(U32.shrn(value,7n),127),128),
     U32.or(U32.and(U32.shrn(value,14n),127),128),U32.or(U32.and(U32.shrn(value,21n),127),128),
     U32.or(U32.shrn(value,28n),112)])

def i32(value: U32) -> List<&2,U32>:
  Con{65,signed(value)}
def get(index: U32) -> List<&2,U32>:
  Con{32,unsigned(index)}
def set(index: U32) -> List<&2,U32>:
  Con{33,unsigned(index)}
def tee(index: U32) -> List<&2,U32>:
  Con{34,unsigned(index)}
def call(index: U32) -> List<&2,U32>:
  Con{16,unsigned(index)}
def load(offset: U32) -> List<&2,U32>:
  Con{40,Con{2,unsigned(offset)}}
def store(offset: U32) -> List<&2,U32>:
  Con{54,Con{2,unsigned(offset)}}
def jump(depth: U32) -> List<&2,U32>:
  Con{12,unsigned(depth)}
def branch(depth: U32) -> List<&2,U32>:
  Con{13,unsigned(depth)}
def select(condition: List<&2,U32>, yes: List<&2,U32>, no: List<&2,U32>) -> List<&2,U32>:
  seq([condition,[4,127],yes,[5],no,[11]])
def when(condition: List<&2,U32>, body: List<&2,U32>) -> List<&2,U32>:
  seq([condition,[4,64],body,[11]])
def eq(left: List<&2,U32>, right: List<&2,U32>) -> List<&2,U32>:
  seq([left,right,[70]])
def binary(op: U32, a: U32, b: U32) -> List<&2,U32>:
  seq([get(a),get(b),[op]])
def invoke(index: U32, a: List<&2,U32>, b: List<&2,U32>) -> List<&2,U32>:
  seq([a,b,call(index)])
def guard(condition: List<&2,U32>) -> List<&2,U32>:
  when(condition,[0])

def size(+bytes: List<&2,U32>) -> List<&2,U32>:
  seq([unsigned(length(bytes)),bytes])

def function(+locals: U32, body: List<&2,U32>) -> List<&2,U32>:
  size(seq([S.choose(List<&2,U32>,U32.is_eq(locals,0),u => [0],u => seq([[1],unsigned(locals),[127]])),body,[11]]))

def word(+value: U32) -> List<&2,U32>:
  [U32.and(value,255),U32.and(U32.shrn(value,8n),255),U32.and(U32.shrn(value,16n),255),U32.shrn(value,24n)]

import Base

type Tree is Data:
  Empty{}
  Chunk{values: List<&2,U32>}
  Join{left: Tree, right: Tree}

type Builder is Data:
  Buffer{limit: U32, length: U32, tree: Tree}

type Error is Data:
  InvalidByte{value: U32}
  Limit{}

def empty(limit: U32) -> Builder:
  Buffer{limit,0,Empty{}}

def length(builder: Builder) -> U32:
  match builder:
    case Buffer{cap,n,t}:
      n

def limit(builder: Builder) -> U32:
  match builder:
    case Buffer{cap,n,t}:
      cap

# Internal helpers. Public builders are obtained through the checked API.
def guard(valid: Bool, error: Error, next: Unit -> Result<Error,U32>) -> Result<Error,U32>:
  match valid:
    case False{}:
      Fail{error}
    case True{}:
      next(Unit{})

def scan(values: List<&2,U32>, +room: U32, +count: U32) -> Result<Error,U32>:
  match values:
    case Nil{}:
      Done{count}
    case Con{+h,t}:
      guard(U32.is_le(h,255),InvalidByte{h},u =>
        guard(U32.is_lt(count,room),Limit{},v => scan(t,room,U32.add(count,1))))

def attach(result: Result<Error,U32>, b: Builder, values: List<&2,U32>) -> Result<Error,Builder>:
  match result b:
    case Fail{err} Buffer{cap,n,t}:
      Fail{err}
    case Done{k} Buffer{cap,n,t}:
      Done{Buffer{cap,U32.add(n,k),Join{t,Chunk{values}}}}

def append(builder: Builder, +values: List<&2,U32>) -> Result<Error,Builder>:
  match builder:
    case Buffer{+cap,+n,+t}:
      attach(scan(values,U32.sub(cap,n),0),Buffer{cap,n,t},values)

def fragment(cap: U32, values: List<&2,U32>) -> Result<Error,Builder>:
  append(empty(cap),values)

def byte(builder: Builder, value: U32) -> Result<Error,Builder>:
  append(builder,Con{value,Nil{}})

def combine(ok: Bool, cap: U32, left_n: U32, right_n: U32, left: Tree, right: Tree) -> Result<Error,Builder>:
  match ok:
    case False{}:
      Fail{Limit{}}
    case True{}:
      Done{Buffer{cap,U32.add(left_n,right_n),Join{left,right}}}

def compose(left: Builder, right: Builder) -> Result<Error,Builder>:
  match left right:
    case Buffer{+cap,+n,a} Buffer{other,+m,b}:
      combine(U32.is_le(m,U32.sub(cap,n)),cap,n,m,a,b)

def emit(tree: Tree, suffix: List<&2,U32>) -> List<&2,U32>:
  match tree:
    case Empty{}:
      suffix
    case Chunk{values}:
      List.append(&2,U32,values,suffix)
    case Join{left,right}:
      emit(left,emit(right,suffix))

def finish(builder: Builder) -> List<&2,U32>:
  match builder:
    case Buffer{cap,n,t}:
      emit(t,Nil{})

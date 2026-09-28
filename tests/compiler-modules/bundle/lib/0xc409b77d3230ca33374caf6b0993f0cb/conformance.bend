import Base
import ./main.bend as B
import ./model.bend as M
import ./bytes.bend as Y

def assert(ok: Bool, name: String) -> IO(Unit):
  match ok:
    case True{}:
      IO.print("PASS " ++ name)
    case False{}:
      IO.die(Unit,1,"FAIL " ++ name)

def texts() -> List<&2,String>:
  ["", "a", "bc", "\r\n", "λ", "🙂", "é", "\0"]

def triple(+a: String, +b: String, +c: String) -> Bool:
  old = B.append(B.empty(),a)
  left = B.compose(B.compose(B.fragment(a),B.fragment(b)),B.fragment(c))
  right = B.compose(B.fragment(a),B.compose(B.fragment(b),B.fragment(c)))
  Bool.and(String.eq(B.finish(left),M.flatten([a,b,c])),
    Bool.and(String.eq(B.finish(right),M.flatten([a,b,c])),
      Bool.and(String.eq(B.finish(B.append(old,b)),M.flatten([a,b])),
        String.eq(B.finish(B.append(B.fragment(a),"")),a))))

def thirds(xs: List<&2,String>, +a: String, +b: String) -> Bool:
  match xs:
    case Nil{}:
      True{}
    case Con{c,tail}:
      Bool.and(triple(a,b,c),thirds(tail,a,b))

def seconds(xs: List<&2,String>, +a: String) -> Bool:
  match xs:
    case Nil{}:
      True{}
    case Con{b,tail}:
      Bool.and(thirds(texts(),a,b),seconds(tail,a))

def all_texts(xs: List<&2,String>) -> Bool:
  match xs:
    case Nil{}:
      True{}
    case Con{a,tail}:
      Bool.and(seconds(texts(),a),all_texts(tail))

def same_bytes(a: List<&2,U32>, b: List<&2,U32>) -> Bool:
  match a b:
    case Nil{} Nil{}:
      True{}
    case Nil{} Con{x,xs}:
      False{}
    case Con{x,xs} Nil{}:
      False{}
    case Con{x,xs} Con{y,ys}:
      Bool.and(U32.is_eq(x,y),same_bytes(xs,ys))

def success(result: Result<Y.Error,Y.Builder>, values: List<&2,U32>, n: U32, cap: U32) -> Bool:
  match result:
    case Fail{err}:
      False{}
    case Done{+b}:
      Bool.and(same_bytes(Y.finish(b),values),Bool.and(U32.is_eq(Y.length(b),n),U32.is_eq(Y.limit(b),cap)))

def is_limit(err: Y.Error) -> Bool:
  match err:
    case Y.Limit{}:
      True{}
    case Y.InvalidByte{x}:
      False{}

def limited(result: Result<Y.Error,Y.Builder>) -> Bool:
  match result:
    case Done{b}:
      False{}
    case Fail{err}:
      is_limit(err)

def is_invalid(err: Y.Error, n: U32) -> Bool:
  match err:
    case Y.Limit{}:
      False{}
    case Y.InvalidByte{x}:
      U32.is_eq(x,n)

def invalid(result: Result<Y.Error,Y.Builder>, n: U32) -> Bool:
  match result:
    case Done{b}:
      False{}
    case Fail{err}:
      is_invalid(err,n)

def byte_states(result: Result<Y.Error,Y.Builder>) -> Bool:
  match result:
    case Fail{err}:
      False{}
    case Done{+old}:
      Bool.and(success(Y.byte(old,255),[0,97,255],3,3),
        Bool.and(success(Y.append(old,[]),[0,97],2,3),
          Bool.and(limited(Y.append(old,[1,2])),
            Bool.and(invalid(Y.byte(old,256),256),
              Bool.and(same_bytes(Y.finish(old),[0,97]),
                Bool.and(success(Y.compose(old,Y.empty(0)),[0,97],2,3),
                  success(Y.compose(Y.empty(3),old),[0,97],2,3)))))))

def pair_bytes(a: Result<Y.Error,Y.Builder>, b: Result<Y.Error,Y.Builder>) -> Bool:
  match a b:
    case Done{+x} Done{+y}:
      Bool.and(success(Y.compose(x,y),[0,97,128,255],4,4),
        Bool.and(limited(Y.compose(y,x)),
          Bool.and(same_bytes(Y.finish(x),[0,97]),same_bytes(Y.finish(y),[128,255]))))
    case Done{x} Fail{err}:
      False{}
    case Fail{err} Done{y}:
      False{}
    case Fail{err} Fail{other}:
      False{}

def capacity_result(result: Result<Y.Error,Y.Builder>, +n: U32) -> Bool:
  match result:
    case Fail{err}:
      False{}
    case Done{+b}:
      Bool.and(U32.is_eq(Y.length(b),n),
        Bool.and(limited(Y.byte(b,0)),success(Y.append(b,[]),List.replicate(U32,U32.to_nat(n),97),n,n)))

def capacity_case(+n: Nat) -> Bool:
  cap = U32.from_nat(n)
  values = List.replicate(U32,n,97)
  capacity_result(Y.fragment(cap,values),U32.from_nat(n))

def capacities(+n: Nat) -> Bool:
  match n:
    case 0n:
      capacity_case(0n)
    case 1n+p:
      Bool.and(capacity_case(1n+p),capacities(p))

def compose_results(a: Result<Y.Error,Y.Builder>, b: Result<Y.Error,Y.Builder>) -> Result<Y.Error,Y.Builder>:
  match a b:
    case Done{x} Done{y}:
      Y.compose(x,y)
    case Fail{e} Done{y}:
      Fail{e}
    case Done{x} Fail{e}:
      Fail{e}
    case Fail{e} Fail{other}:
      Fail{e}

def byte_assoc() -> Bool:
  Bool.and(success(compose_results(compose_results(Y.fragment(6,[0]),Y.fragment(6,[127,128])),Y.fragment(6,[255,10,13])),[0,127,128,255,10,13],6,6),
    success(compose_results(Y.fragment(6,[0]),compose_results(Y.fragment(6,[127,128]),Y.fragment(6,[255,10,13]))),[0,127,128,255,10,13],6,6))

def portable() -> IO(Unit):
  +snapshot = B.fragment("oldλ")
  do IO<Unit>:
    assert(all_texts(texts()),"text-512-triples")
    assert(String.eq(B.finish(B.character(B.fragment("a"),Chr{10})),"a\n"),"character-newline")
    assert(String.eq(B.finish(B.append(snapshot,"new")),"oldλnew"),"snapshot-new")
    assert(String.eq(B.finish(snapshot),"oldλ"),"snapshot-old")
    assert(String.eq(B.finish(B.compose(B.empty(),B.fragment("x"))),"x"),"text-left-identity")
    assert(String.eq(B.finish(B.compose(B.fragment("x"),B.empty())),"x"),"text-right-identity")
    assert(byte_states(Y.fragment(3,[0,97])),"byte-success-failure-persistence")
    assert(pair_bytes(Y.fragment(4,[0,97]),Y.fragment(2,[128,255])),"byte-composition-order-limits")
    assert(byte_assoc(),"byte-associativity-with-sufficient-limits")
    assert(capacities(64n),"byte-capacities-0-through-64")
    assert(invalid(Y.byte(Y.empty(4294967295),4294967295),4294967295),"invalid-max-u32")
    assert(invalid(Y.byte(Y.empty(0),256),256),"invalid-before-capacity")
    assert(limited(Y.combine(U32.is_le(1,U32.sub(4294967295,4294967295)),4294967295,4294967295,1,Y.Empty{},Y.Empty{})),"checked-add-overflow-boundary")

def main() -> IO(Unit):
  do IO<Unit>:
    portable()
    assert(String.eq(B.finish(B.character(B.empty(),Chr{4294967295})),SCon{Chr{4294967295},SNil{}}),"raw-char-preservation")
